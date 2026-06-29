import math

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class LidarAvoidance(Node):

    def __init__(self):
        super().__init__("lidar_avoidance")

        self.scan_sub = self.create_subscription(
            LaserScan,
            "/scan",
            self.scan_callback,
            10
        )

        self.cmd_pub = self.create_publisher(
            Twist,
            "/cmd_vel",
            10
        )

        self.safe_distance = 0.6

        self.forward_speed = 0.25
        self.turn_speed = 0.7

        self.last_state = None

        self.get_logger().info("Lidar avoidance started")

    def get_range_window(self, msg, start_ratio, end_ratio):
        ranges = list(msg.ranges)

        start_index = int(len(ranges) * start_ratio)
        end_index = int(len(ranges) * end_ratio)

        window = ranges[start_index:end_index]

        valid = [
            r for r in window
            if math.isfinite(r) and msg.range_min < r < msg.range_max
        ]

        if valid:
            return min(valid)

        # Nessun ostacolo rilevato nel settore
        return float("inf")

    def get_front_distance(self, msg):
        return self.get_range_window(msg, 0.4, 0.6)

    def get_left_distance(self, msg):
        return self.get_range_window(msg, 0.65, 0.85)

    def get_right_distance(self, msg):
        return self.get_range_window(msg, 0.15, 0.35)

    def decide_motion(self, front_distance, left_distance, right_distance):
        cmd = Twist()

        if front_distance < self.safe_distance:
            left = left_distance if left_distance is not None else 0.0
            right = right_distance if right_distance is not None else 0.0

            if left >= right:
                cmd.angular.z = self.turn_speed
                return "avoiding_left", cmd
            else:
                cmd.angular.z = -self.turn_speed
                return "avoiding_right", cmd

        cmd.linear.x = self.forward_speed
        return "moving_forward", cmd

    def log_state(self, state, front, left, right):
        if state == self.last_state:
            return

        self.get_logger().info(
            f"{state} | front={front} left={left} right={right}"
        )

        self.last_state = state

    def scan_callback(self, msg):
        front_distance = self.get_front_distance(msg)
        left_distance = self.get_left_distance(msg)
        right_distance = self.get_right_distance(msg)

        state, cmd = self.decide_motion(
            front_distance,
            left_distance,
            right_distance
        )

        self.log_state(
            state,
            front_distance,
            left_distance,
            right_distance
        )

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    node = LidarAvoidance()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()