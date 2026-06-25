from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import Command
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from ament_index_python.packages import get_package_share_path


def generate_launch_description():
    pkg_path = get_package_share_path('mobile_robot')

    xacro_file = pkg_path / 'urdf' / 'robot.urdf.xacro'
    world_file = pkg_path / 'worlds' / 'empty.world.sdf'

    robot_description = ParameterValue(
        Command(['xacro ', str(xacro_file)]),
        value_type=str
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_path('ros_gz_sim'),
            '/launch/gz_sim.launch.py'
        ]),
        launch_arguments={
            'gz_args': ['-r ', str(world_file)]
        }.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'robot_description': robot_description}
        ]
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', '/robot_description',
            '-name', 'mobile_robot',
            '-x', '0',
            '-y', '0',
            '-z', '0.3'
        ],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot
    ])