"""Launch localization and optional RViz for one robot."""

import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from mobile_robot.simulation_config import (
    finite_float, normalize_namespace, parameter_document, rviz_document, temporary_yaml, topic,
)


def launch_localization(context):
    value = lambda key: LaunchConfiguration(key).perform(context)
    ns = normalize_namespace(value('namespace'))
    share = get_package_share_directory('mobile_robot')
    with open(os.path.join(share, 'config', 'localization.yaml')) as stream:
        data = yaml.safe_load(stream)
    overrides = {'map_server.ros__parameters.yaml_filename': value('map')}
    for axis in ('x', 'y', 'yaw'):
        overrides['amcl.ros__parameters.initial_pose.' + axis] = finite_float(value(axis))
    params = temporary_yaml(context, parameter_document(data, ns, overrides))
    remaps = [('/tf', topic(ns, 'tf')), ('/tf_static', topic(ns, 'tf_static'))]
    nodes = [Node(package=package, executable=name, name=name, namespace='/' + ns,
                  parameters=[params], remappings=remaps, output='screen')
             for package, name in [('nav2_map_server', 'map_server'), ('nav2_amcl', 'amcl')]]
    nodes.append(Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                      name='lifecycle_manager_localization', namespace='/' + ns,
                      parameters=[params], output='screen'))
    if value('use_rviz').lower() == 'true':
        with open(os.path.join(share, 'rviz', 'mobile_robot.rviz')) as stream:
            rviz = temporary_yaml(context, rviz_document(yaml.safe_load(stream), ns))
        nodes.append(Node(package='rviz2', executable='rviz2', name='rviz2',
                          namespace='/' + ns, arguments=['-d', rviz],
                          parameters=[{'use_sim_time': True}],
                          remappings=remaps, output='screen'))
    return nodes


def generate_launch_description():
    share = get_package_share_directory('mobile_robot')
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value=''),
        DeclareLaunchArgument('map', default_value=os.path.join(share, 'maps', 'slam_world_map.yaml')),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('use_rviz', default_value='true', choices=['true', 'false']),
        OpaqueFunction(function=launch_localization),
    ])
