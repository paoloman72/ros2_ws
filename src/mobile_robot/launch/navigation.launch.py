import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("mobile_robot")

    params_file = os.path.join(
        pkg_share,
        "config",
        "navigation.yaml"
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "default_nav_to_pose_bt_xml",
            default_value=os.path.join(
                get_package_share_directory("nav2_bt_navigator"),
                "behavior_trees",
                "navigate_to_pose_w_replanning_and_recovery.xml",
            ),
            description="Path to the NavigateToPose behavior tree XML",
        ),
        Node(
            package="nav2_planner",
            executable="planner_server",
            name="planner_server",
            output="screen",
            parameters=[params_file],
        ),

        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_navigation",
            output="screen",
            parameters=[params_file],
        ),

        Node(
            package="nav2_controller",
            executable="controller_server",
            name="controller_server",
            output="screen",
            parameters=[params_file],
        ),

        Node(
            package="nav2_behaviors",
            executable="behavior_server",
            name="behavior_server",
            output="screen",
            parameters=[params_file],
        ),

        Node(
            package="nav2_bt_navigator",
            executable="bt_navigator",
            name="bt_navigator",
            output="screen",
            parameters=[params_file, {
                "default_nav_to_pose_bt_xml": ParameterValue(
                    LaunchConfiguration("default_nav_to_pose_bt_xml"),
                    value_type=str,
                ),
            }],
        ),
    ])
