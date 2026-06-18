import rclpy

from rclpy.node import Node
from std_msgs.msg import String


class CounterSubscriber(Node):

    def __init__(self):

        super().__init__('counter_subscriber')

        self.subscription = self.create_subscription(
            String,
            '/counter',
            self.listener_callback,
            10
        )

    def listener_callback(self, msg):

        self.get_logger().info(
            f"Letto: {msg.data}"
        )


def main(args=None):

    rclpy.init(args=args)

    node = CounterSubscriber()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()