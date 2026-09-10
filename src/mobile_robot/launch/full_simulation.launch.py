import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


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
        PythonLaunchDescriptionSource(simulation_launch),
        launch_arguments={'gz_args': LaunchConfiguration('gz_args')}.items()
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
        DeclareLaunchArgument(
            'gz_args',
            default_value='-r ' + os.path.join(
                pkg_share, 'worlds', 'slam_world.world.sdf'),
            description=(
                'Arguments passed to gz sim. For headless (no display, e.g. '
                'in docker) use: gz_args:="-s -r <world file>"'
            ),
        ),
        simulation,
        delayed_bringup,
    ])