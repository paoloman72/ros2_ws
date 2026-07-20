#!/usr/bin/env python3

import math
from typing import Optional, Tuple

import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time

from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from sensor_msgs.msg import LaserScan

from tf2_ros import Buffer, TransformException, TransformListener


class FindFreeSpace(Node):
    """Find a free LiDAR direction and send a NavigateToPose goal."""

    def __init__(self) -> None:
        super().__init__("find_free_space")

        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("map_frame", "map")
        self.declare_parameter("base_frame", "base_link")

        self.declare_parameter("min_goal_distance", 2.0)
        self.declare_parameter("max_goal_distance", 4.0)

        # Half of the required free corridor around the candidate direction.
        # Robot width is 0.5 m; 0.40 gives 0.15 m safety per side.
        self.declare_parameter("corridor_half_width", 0.40)

        # Keep the goal this far before the detected obstacle.
        self.declare_parameter("obstacle_clearance", 0.50)

        # Avoid initially searching behind the robot.
        self.declare_parameter("max_search_angle", math.pi)

        self.scan_topic = str(self.get_parameter("scan_topic").value)
        self.map_frame = str(self.get_parameter("map_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)

        self.min_goal_distance = float(
            self.get_parameter("min_goal_distance").value
        )
        self.max_goal_distance = float(
            self.get_parameter("max_goal_distance").value
        )
        self.corridor_half_width = float(
            self.get_parameter("corridor_half_width").value
        )
        self.obstacle_clearance = float(
            self.get_parameter("obstacle_clearance").value
        )
        self.max_search_angle = float(
            self.get_parameter("max_search_angle").value
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.nav_client = ActionClient(
            self,
            NavigateToPose,
            "/navigate_to_pose",
        )

        self.scan_subscription = self.create_subscription(
            LaserScan,
            self.scan_topic,
            self.scan_callback,
            10,
        )

        self.processing = False
        self.goal_active = False

        self.get_logger().info(
            f"Waiting for scans on {self.scan_topic}"
        )

    def scan_callback(self, scan: LaserScan) -> None:
        if self.processing or self.goal_active:
            return

        self.processing = True

        try:
            candidate = self.find_candidate(scan)

            if candidate is None:
                self.get_logger().warn(
                    "No sufficiently wide free corridor found"
                )
                return

            angle, distance = candidate

            goal = self.create_goal(scan, angle, distance)
            if goal is None:
                return

            self.send_navigation_goal(goal)

        finally:
            self.processing = False

    def find_candidate(
        self,
        scan: LaserScan,
    ) -> Optional[Tuple[float, float]]:
        """Return candidate angle and distance in the laser frame."""

        if not scan.ranges or scan.angle_increment == 0.0:
            return None

        best_candidate: Optional[Tuple[float, float]] = None
        best_score = -math.inf

        # Test distances from farthest to nearest.
        candidate_distances = [
            self.max_goal_distance - index * 0.25
            for index in range(
                int(
                    (self.max_goal_distance - self.min_goal_distance)
                    / 0.25
                ) + 1
            )
        ]

        for center_index, center_range in enumerate(scan.ranges):
            center_angle = (
                scan.angle_min
                + center_index * scan.angle_increment
            )

            if abs(center_angle) > self.max_search_angle:
                continue

            if not self.valid_range(center_range, scan):
                continue

            for candidate_distance in candidate_distances:
                # Angular width required to fit the robot corridor
                # at the selected distance.
                half_angle = math.atan2(
                    self.corridor_half_width,
                    candidate_distance,
                )

                half_window = max(
                    1,
                    int(
                        math.ceil(
                            half_angle / abs(scan.angle_increment)
                        )
                    ),
                )

                start = max(0, center_index - half_window)
                end = min(
                    len(scan.ranges),
                    center_index + half_window + 1,
                )

                required_range = (
                    candidate_distance + self.obstacle_clearance
                )

                corridor_is_free = True

                for measured_range in scan.ranges[start:end]:
                    if not self.valid_range(measured_range, scan):
                        corridor_is_free = False
                        break

                    if measured_range < required_range:
                        corridor_is_free = False
                        break

                if not corridor_is_free:
                    continue

                # Prefer farther goals and directions near the front.
                score = candidate_distance - 0.5 * abs(center_angle)

                if score > best_score:
                    best_score = score
                    best_candidate = (
                        center_angle,
                        candidate_distance,
                    )

                break

        if best_candidate is not None:
            angle, distance = best_candidate
            self.get_logger().info(
                "Free candidate: "
                f"angle={math.degrees(angle):.1f} deg, "
                f"distance={distance:.2f} m"
            )

        return best_candidate

    @staticmethod
    def valid_range(value: float, scan: LaserScan) -> bool:
        return (
            math.isfinite(value)
            and scan.range_min <= value <= scan.range_max
        )

    def create_goal(
        self,
        scan: LaserScan,
        angle: float,
        distance: float,
    ) -> Optional[PoseStamped]:
        """Project the LiDAR candidate from the current robot pose into map."""

        try:
            base_to_map = self.tf_buffer.lookup_transform(
                self.map_frame,
                self.base_frame,
                Time(),
                timeout=Duration(seconds=1.0),
            )
        except TransformException as error:
            self.get_logger().warn(f"Robot TF unavailable: {error}")
            return None

        start_x = base_to_map.transform.translation.x
        start_y = base_to_map.transform.translation.y

        q = base_to_map.transform.rotation

        # Yaw corrente di base_link nel frame map.
        robot_yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )

        # L'angolo del LaserScan è relativo al sensore.
        # Assumiamo per ora che il LiDAR sia orientato come base_link.
        goal_yaw = robot_yaw + angle

        goal_x = start_x + distance * math.cos(goal_yaw)
        goal_y = start_y + distance * math.sin(goal_yaw)

        goal = PoseStamped()
        goal.header.frame_id = self.map_frame
        goal.header.stamp = self.get_clock().now().to_msg()

        goal.pose.position.x = goal_x
        goal.pose.position.y = goal_y
        goal.pose.position.z = 0.0

        # L'orientamento finale segue il vettore partenza → arrivo.
        goal.pose.orientation.z = math.sin(goal_yaw / 2.0)
        goal.pose.orientation.w = math.cos(goal_yaw / 2.0)

        self.get_logger().info(
            "Goal in map: "
            f"x={goal_x:.2f}, y={goal_y:.2f}, "
            f"yaw={math.degrees(goal_yaw):.1f} deg"
        )

        return goal

    def send_navigation_goal(self, pose: PoseStamped) -> None:
        if not self.nav_client.wait_for_server(
            timeout_sec=2.0
        ):
            self.get_logger().error(
                "/navigate_to_pose server unavailable"
            )
            return

        nav_goal = NavigateToPose.Goal()
        nav_goal.pose = pose
        nav_goal.behavior_tree = ""

        self.goal_active = True

        future = self.nav_client.send_goal_async(
            nav_goal,
            feedback_callback=self.feedback_callback,
        )
        future.add_done_callback(
            self.goal_response_callback
        )

    def goal_response_callback(self, future) -> None:
        goal_handle = future.result()

        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(
                "Navigation goal rejected"
            )
            self.goal_active = False
            return

        self.get_logger().info(
            "Navigation goal accepted"
        )

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            self.result_callback
        )

    def feedback_callback(self, feedback_msg) -> None:
        feedback = feedback_msg.feedback

        self.get_logger().info(
            "Navigating: "
            f"remaining={feedback.distance_remaining:.2f} m, "
            f"recoveries={feedback.number_of_recoveries}"
        )

    def result_callback(self, future) -> None:
        wrapped_result = future.result()

        if wrapped_result is None:
            self.get_logger().error(
                "Navigation returned no result"
            )
            self.goal_active = False
            return

        result = wrapped_result.result

        if result.error_code == NavigateToPose.Result.NONE:
            self.get_logger().info(
                "Free-space goal reached"
            )
        else:
            self.get_logger().error(
                "Navigation failed: "
                f"code={result.error_code}, "
                f"message='{result.error_msg}'"
            )

        self.goal_active = False


def main(args=None) -> None:
    rclpy.init(args=args)

    node = FindFreeSpace()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()