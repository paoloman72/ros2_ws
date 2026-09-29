"""Run SLAM for one robot instead of AMCL localization."""

import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushROSNamespace, SetRemap
from mobile_robot.simulation_config import (
    normalize_namespace, parameter_document, temporary_yaml, topic,
)


def launch_slam(context):
    ns = normalize_namespace(LaunchConfiguration('namespace').perform(context))
    with open(os.path.join(get_package_share_directory('mobile_robot'),
                           'config', 'slam_toolbox.yaml')) as stream:
        data = yaml.safe_load(stream)
    data['slam_toolbox']['ros__parameters']['scan_topic'] = topic(ns, 'scan')
    # Match the namespaced lifecycle node created by the upstream launch.
    params = temporary_yaml(context, parameter_document(data, ns))
    return [GroupAction(actions=[
        PushROSNamespace('/' + ns),
        SetRemap(src='/tf', dst=topic(ns, 'tf')),
        SetRemap(src='/tf_static', dst=topic(ns, 'tf_static')),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')),
            launch_arguments={'slam_params_file': params, 'use_sim_time': 'true'}.items()),
    ])]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value=''),
        OpaqueFunction(function=launch_slam),
    ])
