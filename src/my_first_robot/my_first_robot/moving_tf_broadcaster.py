import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class MovingTfBroadcaster(Node):
    def __init__(self):
        super().__init__('moving_tf_broadcaster')

        self.tf_broadcaster = TransformBroadcaster(self)

        self.t = 0.0

        self.timer = self.create_timer(0.05, self.publish_transform)

    def publish_transform(self):
        msg = TransformStamped()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'world'
        msg.child_frame_id = 'robot'

        radius = 2.0
        angular_speed = 0.5

        x = radius * math.cos(self.t)
        y = radius * math.sin(self.t)
        yaw = self.t

        msg.transform.translation.x = x
        msg.transform.translation.y = y
        msg.transform.translation.z = 0.0

        msg.transform.rotation.x = 0.0
        msg.transform.rotation.y = 0.0
        msg.transform.rotation.z = math.sin(yaw / 2.0)
        msg.transform.rotation.w = math.cos(yaw / 2.0)

        self.tf_broadcaster.sendTransform(msg)

        self.t += angular_speed * 0.05


def main(args=None):
    rclpy.init(args=args)

    node = MovingTfBroadcaster()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()