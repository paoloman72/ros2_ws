import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    pkg_share = get_package_share_directory("mobile_robot")

    localization_launch = os.path.join(
        pkg_share,
        "launch",
        "localization.launch.py"
    )

    navigation_launch = os.path.join(
        pkg_share,
        "launch",
        "navigation.launch.py"
    )

    return LaunchDescription([

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                localization_launch
            )
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                navigation_launch
            )
        ),

    ])