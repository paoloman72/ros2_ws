from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_path


def generate_launch_description():
    mobile_robot_path = get_package_share_path('mobile_robot')
    slam_toolbox_path = get_package_share_path('slam_toolbox')

    slam_config = mobile_robot_path / 'config' / 'slam_toolbox.yaml'

    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            slam_toolbox_path,
            '/launch/online_async_launch.py'
        ]),
        launch_arguments={
            'slam_params_file': str(slam_config),
            'use_sim_time': 'true'
        }.items()
    )

    return LaunchDescription([
        slam_toolbox
    ])