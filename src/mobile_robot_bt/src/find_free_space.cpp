#include "mobile_robot_bt/find_free_space.hpp"

#include <cmath>

#include "tf2/exceptions.h"
#include "tf2/time.h"
#include "tf2_ros/buffer.h"

#include <stdexcept>
#include <algorithm>
#include <limits>

namespace mobile_robot_bt
{

FindFreeSpace::FindFreeSpace(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = config.blackboard->get<rclcpp::Node *>("node");

  if (node_ == nullptr) {
    throw std::runtime_error(
      "FindFreeSpace: blackboard entry 'node' is missing or null");
  }

  tf_buffer_ = std::make_shared<tf2_ros::Buffer>(
    node_->get_clock());

  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(
    *tf_buffer_);

  scan_subscription_ = node_->create_subscription<LaserScan>(
    "/scan",
    rclcpp::SensorDataQoS(),
    std::bind(
      &FindFreeSpace::scanCallback,
      this,
      std::placeholders::_1));
}

bool FindFreeSpace::validRange(
    double value,
    const LaserScan& scan)
{
    return std::isfinite(value) &&
           value >= scan.range_min &&
           value <= scan.range_max;
}

std::optional<std::pair<double, double>>
FindFreeSpace::findCandidate(const LaserScan & scan) const
{
  const double min_distance =
    getInput<double>("min_distance").value();

  const double max_distance =
    getInput<double>("max_distance").value();

  const double max_search_angle =
    getInput<double>("max_search_angle").value();

  const double corridor_half_width =
    getInput<double>("corridor_half_width").value();

  const double obstacle_clearance =
    getInput<double>("obstacle_clearance").value();

  std::optional<std::pair<double, double>> best_candidate;
  double best_score = -std::numeric_limits<double>::infinity();

  constexpr double distance_step = 0.25;

  for (std::size_t center_index = 0;
       center_index < scan.ranges.size();
       ++center_index)
  {
    const double center_angle =
      scan.angle_min +
      static_cast<double>(center_index) * scan.angle_increment;

    if (std::abs(center_angle) > max_search_angle) {
      continue;
    }

    if (!validRange(scan.ranges[center_index], scan)) {
      continue;
    }

    for (
      double candidate_distance = max_distance;
      candidate_distance >= min_distance;
      candidate_distance -= distance_step)
    {
      const double half_angle =
        std::atan2(corridor_half_width, candidate_distance);

      const auto half_window = std::max<std::size_t>(
        1,
        static_cast<std::size_t>(
          std::ceil(
            half_angle /
            std::abs(scan.angle_increment))));

      const std::size_t start =
        center_index > half_window
        ? center_index - half_window
        : 0;

      const std::size_t end = std::min(
        scan.ranges.size(),
        center_index + half_window + 1);

      const double required_range =
        candidate_distance + obstacle_clearance;

      bool corridor_is_free = true;

      for (std::size_t index = start; index < end; ++index)
      {
        const double measured_range = scan.ranges[index];

        if (
          !validRange(measured_range, scan) ||
          measured_range < required_range)
        {
          corridor_is_free = false;
          break;
        }
      }

      if (!corridor_is_free) {
        continue;
      }

      // Preferisce goal lontani e, a parità, più frontali.
      const double score =
        candidate_distance -
        0.1 * std::abs(center_angle);

      if (score > best_score)
      {
        best_score = score;
        best_candidate =
          std::make_pair(center_angle, candidate_distance);
      }

      // Per questa direzione abbiamo già trovato
      // la massima distanza valida.
      break;
    }
  }

  return best_candidate;
}

std::optional<geometry_msgs::msg::PoseStamped>
FindFreeSpace::createGoal(
    double angle,
    double distance)
{
    const auto map_frame =
        getInput<std::string>("map_frame").value();

    const auto base_frame =
        getInput<std::string>("base_frame").value();

    geometry_msgs::msg::TransformStamped base_to_map;

    try
    {
        base_to_map = tf_buffer_->lookupTransform(
            map_frame,
            base_frame,
            tf2::TimePointZero);
    }
    catch(const tf2::TransformException & ex)
    {
        RCLCPP_WARN(
            node_->get_logger(),
            "Robot TF unavailable: %s",
            ex.what());

        return std::nullopt;
    }

    const double start_x =
        base_to_map.transform.translation.x;

    const double start_y =
        base_to_map.transform.translation.y;

    const auto & q =
        base_to_map.transform.rotation;

    // Yaw corrente del robot
    const double robot_yaw =
        std::atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z));

    // Angolo assoluto del goal
    const double goal_yaw =
        robot_yaw + angle;

    const double goal_x =
        start_x + distance * std::cos(goal_yaw);

    const double goal_y =
        start_y + distance * std::sin(goal_yaw);

    geometry_msgs::msg::PoseStamped goal;

    goal.header.frame_id = map_frame;
    goal.header.stamp = node_->now();

    goal.pose.position.x = goal_x;
    goal.pose.position.y = goal_y;
    goal.pose.position.z = 0.0;

    goal.pose.orientation.x = 0.0;
    goal.pose.orientation.y = 0.0;
    goal.pose.orientation.z = std::sin(goal_yaw * 0.5);
    goal.pose.orientation.w = std::cos(goal_yaw * 0.5);

    RCLCPP_INFO(
        node_->get_logger(),
        "Goal in map: x=%.2f y=%.2f yaw=%.1f deg",
        goal_x,
        goal_y,
        goal_yaw * 180.0 / M_PI);

    return goal;
}

BT::PortsList FindFreeSpace::providedPorts()
{
  return {
    BT::OutputPort<geometry_msgs::msg::PoseStamped>(
      "goal",
      "Generated navigation goal"),

    BT::InputPort<double>(
      "min_distance",
      2.0,
      "Minimum target distance in meters"),

    BT::InputPort<double>(
      "max_distance",
      4.0,
      "Maximum target distance in meters"),

    BT::InputPort<double>(
      "max_search_angle",
      3.14159,
      "Maximum absolute search angle in radians"),

    BT::InputPort<double>(
      "corridor_half_width",
      0.40,
      "Half width of the required free corridor"),

    BT::InputPort<double>(
      "obstacle_clearance",
      0.50,
      "Clearance from obstacles in meters"),

    BT::InputPort<std::string>(
      "map_frame",
      "map",
      "Global map frame"),

    BT::InputPort<std::string>(
      "base_frame",
      "base_link",
      "Robot base frame")
  };
}

void FindFreeSpace::scanCallback(
  const LaserScan::SharedPtr scan)
{
  std::lock_guard<std::mutex> lock(scan_mutex_);
  latest_scan_ = scan;
}

BT::NodeStatus FindFreeSpace::onStart()
{
  RCLCPP_INFO(
    node_->get_logger(),
    "FindFreeSpace: searching for a free target");

  return tryCreateGoal();
}

BT::NodeStatus FindFreeSpace::onRunning()
{
  return tryCreateGoal();
}

void FindFreeSpace::onHalted()
{
  RCLCPP_WARN(
    node_->get_logger(),
    "FindFreeSpace halted");
}

BT::NodeStatus FindFreeSpace::tryCreateGoal()
{
  LaserScan::SharedPtr scan;

  {
    std::lock_guard<std::mutex> lock(scan_mutex_);
    scan = latest_scan_;
  }

  if (!scan) {
    return BT::NodeStatus::RUNNING;
  }

  const auto candidate = findCandidate(*scan);

  if (!candidate) {
    RCLCPP_WARN(
      node_->get_logger(),
      "FindFreeSpace: no valid candidate found");

    return BT::NodeStatus::FAILURE;
  }

  const auto [angle, distance] = candidate.value();

  RCLCPP_INFO(
    node_->get_logger(),
    "Candidate: angle %.1f deg distance %.2f",
    angle * 180.0 / M_PI,
    distance);

  const auto goal = createGoal(angle, distance);

  if (!goal) {
    return BT::NodeStatus::RUNNING;
  }

  setOutput("goal", goal.value());

  RCLCPP_INFO(
    node_->get_logger(),
    "FindFreeSpace: goal generated");

  std::lock_guard<std::mutex> lock(scan_mutex_);
  latest_scan_.reset();

  return BT::NodeStatus::SUCCESS;
}

}  // namespace mobile_robot_bt