"""Spawn one robot into an already running world; do not start Gazebo."""

import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from mobile_robot.simulation_config import (
    bridge_entries, finite_float, model_name, normalize_namespace, temporary_yaml, topic,
)


def launch_robot(context):
    value = lambda key: LaunchConfiguration(key).perform(context)
    ns = normalize_namespace(value('namespace'))
    name = model_name(ns, value('robot_name'))
    pose = {key: str(finite_float(value(key))) for key in ('x', 'y', 'z', 'yaw')}
    share = get_package_share_directory('mobile_robot')
    description = xacro.process_file(
        os.path.join(share, 'urdf', 'robot.urdf.xacro'),
        mappings={'robot_name': name, 'topic_prefix': '/' + ns if ns else ''},
    ).toxml()
    remaps = [('/tf', topic(ns, 'tf')), ('/tf_static', topic(ns, 'tf_static'))]
    return [
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             namespace='/' + ns, parameters=[{'robot_description': description,
                                             'use_sim_time': True}], remappings=remaps),
        Node(package='ros_gz_sim', executable='create', namespace='/' + ns,
             name='spawn_robot', output='screen', arguments=[
                 '-topic', topic(ns, 'robot_description'), '-name', name,
                 '-allow_renaming', 'false', '-x', pose['x'], '-y', pose['y'],
                 '-z', pose['z'], '-Y', pose['yaw']]),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             namespace='/' + ns, name='robot_bridge', output='screen',
             parameters=[{'config_file': temporary_yaml(context, bridge_entries(ns))}]),
        Node(package='tf2_ros', executable='static_transform_publisher',
             namespace='/' + ns, name='scan_tf', output='screen',
             parameters=[{'use_sim_time': True}], remappings=remaps,
             arguments=['--x', '0', '--y', '0', '--z', '0', '--roll', '0',
                        '--pitch', '0', '--yaw', '0', '--frame-id', 'lidar_link',
                        '--child-frame-id', name + '/base_link/lidar_sensor']),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value=''),
        DeclareLaunchArgument('robot_name', default_value='',
                              description='Default: namespace with / replaced by _, or mobile_robot'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.3'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        OpaqueFunction(function=launch_robot),
    ])
