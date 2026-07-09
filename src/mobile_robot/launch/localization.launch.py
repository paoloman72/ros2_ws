import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("mobile_robot")

    params_file = os.path.join(
        pkg_share,
        "config",
        "localization.yaml"
    )

    rviz_config = os.path.join(
        pkg_share,
        "rviz",
        "mobile_robot.rviz"
    )

    return LaunchDescription([
        Node(
            package="nav2_map_server",
            executable="map_server",
            name="map_server",
            output="screen",
            parameters=[params_file],
        ),

        Node(
            package="nav2_amcl",
            executable="amcl",
            name="amcl",
            output="screen",
            parameters=[params_file],
        ),

        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_localization",
            output="screen",
            parameters=[params_file],
        ),

        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="screen",
            arguments=[
                "-d",
                rviz_config
            ],
            parameters=[
                {"use_sim_time": True}
            ],
        ),
    ])