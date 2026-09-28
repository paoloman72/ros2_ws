"""Regression checks for root operation and isolation between robot instances."""

from pathlib import Path
import unittest

import yaml
from mobile_robot.simulation_config import (
    bridge_entries, finite_float, model_name, normalize_namespace,
    parameter_document, rviz_document, topic,
)

PACKAGE = Path(__file__).resolve().parents[1]


def read_yaml(path):
    with (PACKAGE / path).open() as stream:
        return yaml.safe_load(stream)


class SimulationConfigTest(unittest.TestCase):
    """Check the runtime data used by bridges, Nav2, AMCL and RViz."""

    def test_root_bridge_preserves_interfaces(self):
        entries = bridge_entries('')
        self.assertEqual([e['ros_topic_name'] for e in entries],
                         ['/cmd_vel', '/odom', '/tf', '/scan', '/imu'])
        self.assertTrue(all(e['ros_topic_name'] == e['gz_topic_name'] for e in entries))
        self.assertEqual(entries[0]['direction'], 'ROS_TO_GZ')
        self.assertTrue(all(e['direction'] == 'GZ_TO_ROS' for e in entries[1:]))
        self.assertEqual(model_name(''), 'mobile_robot')

    def test_two_bridges_are_disjoint_on_both_transports(self):
        for key in ('ros_topic_name', 'gz_topic_name'):
            first = {e[key] for e in bridge_entries('robot1')}
            second = {e[key] for e in bridge_entries('robot2')}
            self.assertFalse(first & second)
            self.assertNotIn('/clock', first | second)
        self.assertEqual(model_name('fleet/robot1'), 'fleet_robot1')
        self.assertEqual(model_name('robot1', 'pluto'), 'pluto')

    def test_root_nav_parameters_are_unchanged(self):
        original = read_yaml('config/navigation.yaml')
        result = parameter_document(original, '')
        for name in ('planner_server', 'controller_server', 'bt_navigator',
                     'behavior_server', 'lifecycle_manager_navigation'):
            self.assertEqual(result['/' + name], original[name])
        for name in ('global_costmap', 'local_costmap'):
            self.assertEqual(result[f'/{name}/{name}'], original[name][name])

    def test_costmap_selectors_and_topics_use_robot_namespace(self):
        original = read_yaml('config/navigation.yaml')
        result = parameter_document(original, '/fleet/robot1/')
        local = result['/fleet/robot1/local_costmap/local_costmap']['ros__parameters']
        glob = result['/fleet/robot1/global_costmap/global_costmap']['ros__parameters']
        self.assertEqual(local['obstacle_layer']['scan']['topic'], '/fleet/robot1/scan')
        self.assertEqual(glob['static_layer']['map_topic'], '/fleet/robot1/map')
        self.assertEqual(local['robot_base_frame'], 'base_link')
        self.assertEqual(glob['global_frame'], 'map')
        behavior = result['/fleet/robot1/behavior_server']['ros__parameters']
        self.assertEqual(behavior['costmap_topic'], '/fleet/robot1/local_costmap/costmap_raw')
        self.assertEqual(original, read_yaml('config/navigation.yaml'))

    def test_amcl_pose_and_map_are_per_instance(self):
        result = parameter_document(read_yaml('config/localization.yaml'), 'robot2', {
            'amcl.ros__parameters.initial_pose.x': 1.5,
            'amcl.ros__parameters.initial_pose.yaw': 0.8,
            'map_server.ros__parameters.yaml_filename': '/maps/test.yaml',
        })
        amcl = result['/robot2/amcl']['ros__parameters']
        self.assertEqual(amcl['initial_pose']['x'], 1.5)
        self.assertEqual(amcl['initial_pose']['yaw'], 0.8)
        self.assertEqual(amcl['scan_topic'], '/robot2/scan')
        self.assertEqual(result['/robot2/map_server']['ros__parameters']['yaml_filename'],
                         '/maps/test.yaml')

    def test_rviz_root_and_namespaced_topics(self):
        original = read_yaml('rviz/mobile_robot.rviz')
        self.assertEqual(rviz_document(original, ''), original)
        result = rviz_document(original, 'robot1')['Visualization Manager']
        self.assertEqual(result['Global Options']['Fixed Frame'], 'map')
        scan = next(d for d in result['Displays'] if d['Name'] == 'LaserScan')
        self.assertEqual(scan['Topic']['Value'], '/robot1/scan')
        goal = next(t for t in result['Tools'] if t['Class'].endswith('/SetGoal'))
        self.assertEqual(goal['Topic']['Value'], '/robot1/goal_pose')

    def test_invalid_names_and_coordinates_are_rejected(self):
        for ns in ('robot 1', 'robot//one', '1robot', 'robot/../other'):
            with self.assertRaises(ValueError):
                normalize_namespace(ns)
        with self.assertRaises(ValueError):
            model_name('', 'robot/name')
        for value in ('nan', 'inf', '-inf'):
            with self.assertRaises(ValueError):
                finite_float(value)
        self.assertEqual(topic('/', 'scan'), '/scan')
        self.assertEqual(finite_float('1.2'), 1.2)


if __name__ == '__main__':
    unittest.main()
