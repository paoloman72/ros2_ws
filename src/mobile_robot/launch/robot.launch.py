"""Spawn and bring up one robot in an existing Gazebo world."""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_share = get_package_share_directory("mobile_robot")

    simulation_launch = os.path.join(
        pkg_share,
        "launch",
        "spawn_robot.launch.py",
    )

    bringup_launch = os.path.join(
        pkg_share,
        "launch",
        "bringup.launch.py",
    )

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(simulation_launch),
    )

    delayed_bringup = TimerAction(
        period=8.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(bringup_launch)
            )
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value=''),
        DeclareLaunchArgument('robot_name', default_value=''),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.3'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('use_rviz', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('map', default_value=os.path.join(pkg_share, 'maps', 'slam_world_map.yaml')),
        DeclareLaunchArgument('nav_groot_port', default_value='1667'),
        DeclareLaunchArgument('default_nav_to_pose_bt_xml', default_value=os.path.join(
            get_package_share_directory('nav2_bt_navigator'), 'behavior_trees',
            'navigate_to_pose_w_replanning_and_recovery.xml')),
        simulation,
        delayed_bringup,
    ])
