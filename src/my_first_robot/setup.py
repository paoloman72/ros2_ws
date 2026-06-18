from setuptools import find_packages, setup
from glob import glob

package_name = 'my_first_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
        glob('launch/*.launch.py')
),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='paoloman72',
    maintainer_email='paoloman72@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        	'counter_publisher = my_first_robot.counter_publisher:main',
            'counter_subscriber = my_first_robot.counter_subscriber:main',
            'turtle_avoidance = my_first_robot.turtle_avoidance:main',
            'turtle_spawner = my_first_robot.turtle_spawner:main',
        ],
    }
)
