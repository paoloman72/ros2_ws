"""Start one Gazebo world and one shared ROS clock bridge."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('mobile_robot')
    return LaunchDescription([
        DeclareLaunchArgument('gz_args', default_value='-r ' + os.path.join(
            share, 'worlds', 'slam_world.world.sdf')),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': LaunchConfiguration('gz_args')}.items()),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             name='clock_bridge', namespace='/',
             arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
             output='screen'),
    ])
