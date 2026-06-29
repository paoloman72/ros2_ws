import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class TeleopKeyboard(Node):
    def __init__(self):
        super().__init__('teleop_keyboard')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.linear_speed = 0.3
        self.angular_speed = 0.8

        self.get_logger().info('Teleop keyboard started')
        self.print_instructions()

    def print_instructions(self):
        print()
        print('Keyboard controls:')
        print('  w : forward')
        print('  s : backward')
        print('  a : rotate left')
        print('  d : rotate right')
        print('  x : stop')
        print('  q : quit')
        print()

    def publish_cmd(self, linear_x, angular_z):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.publisher.publish(msg)

    def run(self):
        old_settings = termios.tcgetattr(sys.stdin)

        try:
            tty.setcbreak(sys.stdin.fileno())

            while rclpy.ok():
                key = sys.stdin.read(1)

                if key == 'w':
                    self.publish_cmd(self.linear_speed, 0.0)
                elif key == 's':
                    self.publish_cmd(-self.linear_speed, 0.0)
                elif key == 'a':
                    self.publish_cmd(0.0, self.angular_speed)
                elif key == 'd':
                    self.publish_cmd(0.0, -self.angular_speed)
                elif key == 'x':
                    self.publish_cmd(0.0, 0.0)
                elif key == 'q':
                    self.publish_cmd(0.0, 0.0)
                    break

        finally:
            self.publish_cmd(0.0, 0.0)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def main(args=None):
    rclpy.init(args=args)

    node = TeleopKeyboard()

    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()