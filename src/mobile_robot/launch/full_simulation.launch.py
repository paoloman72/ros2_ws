import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_share = get_package_share_directory("mobile_robot")

    simulation_launch = os.path.join(
        pkg_share,
        "launch",
        "gazebo.launch.py",
    )

    bringup_launch = os.path.join(
        pkg_share,
        "launch",
        "bringup.launch.py",
    )

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(simulation_launch)
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
        simulation,
        delayed_bringup,
    ])