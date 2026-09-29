"""Configuration shared by the single-robot and namespaced launch paths."""

import copy
import math
import re


def normalize_namespace(value):
    """Accept root or slash-separated ROS namespace tokens."""
    namespace = value.strip('/')
    if namespace and not all(
        re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', token)
        for token in namespace.split('/')
    ):
        raise ValueError(f'Invalid robot namespace: {value!r}')
    return namespace


def topic(namespace, name):
    """Return an absolute topic, including for nodes nested in costmaps."""
    namespace = normalize_namespace(namespace)
    return '/' + '/'.join(part for part in (namespace, name.strip('/')) if part)


def model_name(namespace, requested=''):
    """Keep the original model name at root; derive a unique name otherwise."""
    name = requested or normalize_namespace(namespace).replace('/', '_') or 'mobile_robot'
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
        raise ValueError(f'Invalid Gazebo robot name: {name!r}')
    return name


def finite_float(value):
    """Reject invalid spawn/localization coordinates before launching processes."""
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f'Expected a finite coordinate, got {value!r}')
    return result


def parameter_document(data, namespace, overrides=None):
    """Scope node selectors and robot topics without rewriting TF frame IDs."""
    namespace = normalize_namespace(namespace)
    data = copy.deepcopy(data)
    robot_topics = {
        '/scan', '/odom', '/map', '/cmd_vel', '/imu',
        '/local_costmap/costmap_raw', '/local_costmap/published_footprint',
        '/global_costmap/costmap_raw', '/global_costmap/published_footprint',
    }

    def rewrite(value):
        if isinstance(value, dict):
            return {key: rewrite(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        if isinstance(value, str) and value in robot_topics:
            return topic(namespace, value)
        return value

    data = rewrite(data)
    for path, value in (overrides or {}).items():
        target = data
        keys = path.split('.')
        for key in keys[:-1]:
            target = target.setdefault(key, {})
        target[keys[-1]] = value

    # Fully qualified selectors also cover Nav2's internally created costmap nodes.
    result = {}

    def collect(node, parts):
        if 'ros__parameters' in node:
            result[topic(namespace, '/'.join(parts))] = node
        else:
            for key, child in node.items():
                collect(child, parts + [key])

    collect(data, [])
    return result


def bridge_entries(namespace):
    """Use explicit Gazebo/ROS topic pairs; /clock belongs to world launch."""
    specs = [
        ('cmd_vel', 'geometry_msgs/msg/Twist', 'gz.msgs.Twist', 'ROS_TO_GZ'),
        ('odom', 'nav_msgs/msg/Odometry', 'gz.msgs.Odometry', 'GZ_TO_ROS'),
        ('tf', 'tf2_msgs/msg/TFMessage', 'gz.msgs.Pose_V', 'GZ_TO_ROS'),
        ('scan', 'sensor_msgs/msg/LaserScan', 'gz.msgs.LaserScan', 'GZ_TO_ROS'),
        ('imu', 'sensor_msgs/msg/Imu', 'gz.msgs.IMU', 'GZ_TO_ROS'),
    ]
    return [dict(ros_topic_name=topic(namespace, name),
                 gz_topic_name=topic(namespace, name),
                 ros_type_name=ros_type, gz_type_name=gz_type, direction=direction)
            for name, ros_type, gz_type, direction in specs]


def rviz_document(data, namespace):
    """Scope configured topics while retaining local frame names such as map."""
    if isinstance(data, dict):
        return {key: (topic(namespace, value)
                      if key == 'Value' and isinstance(value, str) and value.startswith('/')
                      else rviz_document(value, namespace))
                for key, value in data.items()}
    if isinstance(data, list):
        return [rviz_document(value, namespace) for value in data]
    return data


def temporary_yaml(context, document):
    """Keep runtime configuration until launch shutdown, then remove it."""
    from pathlib import Path
    import tempfile
    import yaml
    from launch.actions import OpaqueFunction
    from launch.event_handlers import OnShutdown

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as stream:
        yaml.safe_dump(document, stream, sort_keys=False)
        filename = stream.name

    def cleanup(_context):
        Path(filename).unlink(missing_ok=True)
        return []

    context.register_event_handler(OnShutdown(on_shutdown=[OpaqueFunction(function=cleanup)]))
    return filename
