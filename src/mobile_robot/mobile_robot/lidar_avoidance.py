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

        self.last_state = None

        self.get_logger().info("Lidar avoidance started")

    def scan_callback(self, msg):

        ranges = list(msg.ranges)

        if len(ranges) == 0:
            return

        center = len(ranges) // 2

        window = 20

        front = ranges[center-window:center+window]

        valid = [
            r for r in front
            if msg.range_min < r < msg.range_max
        ]

        if len(valid) == 0:
            return

        min_distance = min(valid)

        cmd = Twist()

        if min_distance < self.safe_distance:
            state = "avoiding"
            cmd.angular.z = 0.7
        else:
            state = "moving_forward"
            cmd.linear.x = 0.25

        if state != self.last_state:
            if state == "avoiding":
                self.get_logger().info(
                    f"Obstacle detected at {min_distance:.2f} m, steering left"
                )
            else:
                self.get_logger().info(
                    f"Path clear, moving forward. Front min distance: {min_distance:.2f} m"
                )

            self.last_state = state

        self.cmd_pub.publish(cmd)


def main(args=None):

    rclpy.init(args=args)

    node = LidarAvoidance()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()