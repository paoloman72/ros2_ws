import math
import random

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import Twist
from turtlesim_msgs.action import RotateAbsolute
from turtlesim_msgs.msg import Pose

# Turtle avoidance class definition:
#   this class implements a simple wall avoidance behavior for a turtle in the turtlesim environment.
#   The turtle moves forward until it detects a wall, then rotates to a safe heading away from the wall.
class TurtleAvoidance(Node):

    def __init__(self):
        super().__init__('turtle_avoidance')

        self.turtle_name = 'turtle1'

        self.cmd_pub = self.create_publisher(
            Twist,
            f'/{self.turtle_name}/cmd_vel',
            10
        )

        self.pose_sub = self.create_subscription(
            Pose,
            f'/{self.turtle_name}/pose',
            self.pose_callback,
            10
        )

        self.rotate_client = ActionClient(
            self,
            RotateAbsolute,
            f'/{self.turtle_name}/rotate_absolute'
        )

        self.pose = None
        # Simple two-state controller: move straight, then rotate when near a wall.
        self.state = 'forward'
        # Keep moving forward briefly after a turn to avoid immediate re-detection.
        self.cooldown_ticks = 0
        self.goal_in_progress = False

        self.timer = self.create_timer(0.1, self.control_loop)

    def pose_callback(self, msg):
        self.pose = msg

    def detect_wall(self):
        if self.pose is None:
            return None

        # Turtlesim world is 11x11; keep a safety margin from each boundary.
        margin = 1.0

        if self.pose.x < margin:
            return 'left'
        if self.pose.x > 11.0 - margin:
            return 'right'
        if self.pose.y < margin:
            return 'bottom'
        if self.pose.y > 11.0 - margin:
            return 'top'

        return None

    def safe_heading_for_wall(self, wall):
        # Heading points away from the detected wall.
        if wall == 'left':
            return 0.0
        if wall == 'right':
            return math.pi
        if wall == 'bottom':
            return math.pi / 2
        if wall == 'top':
            return -math.pi / 2

        return 0.0

    def normalize_angle(self, angle):
        # Wrap angle into [-pi, pi] for stable rotate goals.
        return math.atan2(math.sin(angle), math.cos(angle))

    def control_loop(self):
        if self.pose is None:
            return

        cmd = Twist()

        if self.state == 'forward':

            if self.cooldown_ticks > 0:
                self.cooldown_ticks -= 1
                cmd.linear.x = 1.5
                self.cmd_pub.publish(cmd)
                return

            wall = self.detect_wall()

            if wall is not None:
                # Stop before sending a new absolute rotation goal.
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
                self.cmd_pub.publish(cmd)

                desired_heading = self.safe_heading_for_wall(wall)

                jitter = random.uniform(
                    -math.radians(20),
                    math.radians(20)
                )

                desired_heading = self.normalize_angle(
                    desired_heading + jitter
                )

                self.get_logger().info(
                    f"Wall {wall}. Rotate to "
                    f"{math.degrees(desired_heading):.1f} deg"
                )

                self.send_rotate_goal(desired_heading)
                self.state = 'rotating'
                return

            cmd.linear.x = 2.0
            cmd.angular.z = 0.0
            self.cmd_pub.publish(cmd)

        elif self.state == 'rotating':
            return

    def send_rotate_goal(self, theta):
        if self.goal_in_progress:
            return

        # Prevent overlapping action requests.
        self.goal_in_progress = True

        goal_msg = RotateAbsolute.Goal()
        goal_msg.theta = theta

        self.rotate_client.wait_for_server()

        send_goal_future = self.rotate_client.send_goal_async(
            goal_msg,
            feedback_callback=self.rotate_feedback_callback
        )

        send_goal_future.add_done_callback(
            self.rotate_goal_response_callback
        )

    def rotate_goal_response_callback(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().warn('Rotate goal rejected')
            self.goal_in_progress = False
            self.state = 'forward'
            return

        self.get_logger().info('Rotate goal accepted')

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            self.rotate_result_callback
        )

    def rotate_feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback

        self.get_logger().debug(
            f"Remaining angle: {feedback.remaining:.2f}"
        )

    def rotate_result_callback(self, future):
        result = future.result().result

        self.get_logger().info(
            f"Rotate completed. Delta: {result.delta:.2f}"
        )

        self.goal_in_progress = False
        # Small forward-only grace period after rotating.
        self.cooldown_ticks = 10
        self.state = 'forward'


def main(args=None):
    rclpy.init(args=args)

    node = TurtleAvoidance()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
