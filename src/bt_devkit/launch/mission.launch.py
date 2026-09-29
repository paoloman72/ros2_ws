"""Launch an unchanged bt_executor with the selected robot's ROS interfaces."""

from pathlib import Path
import re

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_mission(context):
    def value(name):
        return LaunchConfiguration(name).perform(context)

    namespace = value('robot').strip('/')
    if namespace and not all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', token)
                             for token in namespace.split('/')):
        raise ValueError('robot must be a ROS namespace, for example robot1')
    mission = value('mission')
    tree = Path(value('tree'))
    if not tree.is_absolute():
        tree = Path(get_package_share_directory(mission)) / 'behavior_trees' / tree
    plugin = value('plugin')
    if not plugin:
        plugin = str(Path(get_package_prefix(mission)) / 'lib' / mission /
                     f'lib{mission}_nodes.so')
    if not tree.is_file():
        raise ValueError(f'Behavior tree not found: {tree}')
    if not Path(plugin).is_file():
        raise ValueError(f'Plugin not found: {plugin}; build the mission or set plugin:=/path/library.so')
    port = int(value('port'))
    if not 1 <= port <= 65534:
        raise ValueError('port must be in 1..65534; Groot uses this port and the next one')
    tick = int(value('tick_period_ms'))
    if tick <= 0:
        raise ValueError('tick_period_ms must be positive')

    def target(name):
        return '/' + '/'.join(part for part in (namespace, name) if part)

    return [Node(
        package='bt_devkit', executable='bt_executor', namespace='/' + namespace,
        output='screen',
        # Process-wide rules also cover TF listeners constructed inside plugins.
        remappings=[('/tf', target('tf')), ('/tf_static', target('tf_static')),
                    ('/scan', target('scan'))],
        parameters=[{
            'bt_xml': str(tree), 'plugin_library': plugin,
            'use_sim_time': value('use_sim_time') == 'true',
            'groot_enabled': value('groot') == 'true', 'groot_port': port,
            'tick_period_ms': tick,
            'ready_file': value('ready_file'), 'start_file': value('start_file'),
        }],
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('mission', description='Installed mission package, e.g. wander_mission'),
        DeclareLaunchArgument('robot', default_value='', description='Robot namespace; empty means root'),
        DeclareLaunchArgument('tree', default_value='main.xml',
                              description='Tree under behavior_trees, or an absolute XML path'),
        DeclareLaunchArgument('plugin', default_value='',
                              description='Optional absolute .so path; default follows bt_devkit_add_mission'),
        DeclareLaunchArgument('groot', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('port', default_value='1669'),
        DeclareLaunchArgument('use_sim_time', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('tick_period_ms', default_value='100'),
        DeclareLaunchArgument('ready_file', default_value=''),
        DeclareLaunchArgument('start_file', default_value=''),
        OpaqueFunction(function=launch_mission),
    ])
