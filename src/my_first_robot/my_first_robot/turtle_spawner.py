import rclpy
from rclpy.node import Node

from turtlesim_msgs.srv import Spawn


class TurtleSpawner(Node):

    def __init__(self):
        super().__init__('turtle_spawner')

        self.client = self.create_client(
            Spawn,
            '/spawn'
        )

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Aspetto il service /spawn...')

        request = Spawn.Request()
        request.x = 5.0
        request.y = 5.0
        request.theta = 0.0
        request.name = 'bob'

        self.future = self.client.call_async(request)
        self.future.add_done_callback(self.spawn_done_callback)

    def spawn_done_callback(self, future):
        response = future.result()
        self.get_logger().info(
            f"Tartaruga creata: {response.name}"
        )


def main(args=None):
    rclpy.init(args=args)

    node = TurtleSpawner()

    rclpy.spin_until_future_complete(node, node.future)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()