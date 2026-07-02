import os
from setuptools import find_packages, setup
from glob import glob

package_name = 'mobile_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
        glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'),
        glob('urdf/*')),
        (os.path.join('share', package_name, 'worlds'),
        glob('worlds/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),       
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='paoloman',
    maintainer_email='p.maninetti@reply.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'teleop_keyboard = mobile_robot.teleop_keyboard:main',
            'lidar_avoidance = mobile_robot.lidar_avoidance:main',
        ],
    },
)
