"""Launch an isolated Nav2 stack using the existing navigation tuning."""

import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from mobile_robot.simulation_config import normalize_namespace, parameter_document, temporary_yaml, topic


def launch_navigation(context):
    value = lambda key: LaunchConfiguration(key).perform(context)
    ns = normalize_namespace(value('namespace'))
    port = int(value('nav_groot_port'))
    if not 1 <= port <= 65534:
        raise ValueError('nav_groot_port must be between 1 and 65534 (two consecutive ports)')
    with open(os.path.join(get_package_share_directory('mobile_robot'),
                           'config', 'navigation.yaml')) as stream:
        data = yaml.safe_load(stream)
    params = temporary_yaml(context, parameter_document(data, ns, {
        'bt_navigator.ros__parameters.default_nav_to_pose_bt_xml': value('default_nav_to_pose_bt_xml'),
        'bt_navigator.ros__parameters.navigate_to_pose.groot_server_port': port,
    }))
    remaps = [('/tf', topic(ns, 'tf')), ('/tf_static', topic(ns, 'tf_static'))]
    nodes = [Node(package=package, executable=name, name=name, namespace='/' + ns,
                  parameters=[params], remappings=remaps, output='screen')
             for package, name in [
                 ('nav2_planner', 'planner_server'),
                 ('nav2_controller', 'controller_server'),
                 ('nav2_behaviors', 'behavior_server'),
                 ('nav2_bt_navigator', 'bt_navigator')]]
    nodes.append(Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                      name='lifecycle_manager_navigation', namespace='/' + ns,
                      parameters=[params], output='screen'))
    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value=''),
        DeclareLaunchArgument('nav_groot_port', default_value='1667'),
        DeclareLaunchArgument('default_nav_to_pose_bt_xml', default_value=os.path.join(
            get_package_share_directory('nav2_bt_navigator'), 'behavior_trees',
            'navigate_to_pose_w_replanning_and_recovery.xml')),
        OpaqueFunction(function=launch_navigation),
    ])
