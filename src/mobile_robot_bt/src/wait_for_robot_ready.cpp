#include "mobile_robot_bt/wait_for_robot_ready.hpp"

#include <functional>
#include <stdexcept>

#include "tf2/exceptions.h"
#include "tf2/time.h"

namespace mobile_robot_bt
{

WaitForRobotReady::WaitForRobotReady(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = config.blackboard->get<rclcpp::Node *>("node");

  if (node_ == nullptr) {
    throw std::runtime_error(
      "WaitForRobotReady: blackboard entry 'node' is missing or null");
  }

  tf_buffer_ = std::make_shared<tf2_ros::Buffer>(node_->get_clock());
  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
}

BT::PortsList WaitForRobotReady::providedPorts()
{
  return {
    BT::InputPort<std::string>(
      "scan_topic", "/scan", "LaserScan topic to wait for"),
    BT::InputPort<std::string>(
      "map_frame", "map", "Global map frame"),
    BT::InputPort<std::string>(
      "base_frame", "base_link", "Robot base frame"),
    BT::InputPort<double>(
      "timeout", 15.0, "Readiness timeout in seconds")
  };
}

void WaitForRobotReady::scanCallback(const LaserScan::SharedPtr)
{
  std::lock_guard<std::mutex> lock(mutex_);
  scan_received_ = true;
}

BT::NodeStatus WaitForRobotReady::onStart()
{
  const auto scan_topic = getInput<std::string>("scan_topic");
  const auto timeout = getInput<double>("timeout");

  if (!scan_topic || !timeout || timeout.value() < 0.0) {
    RCLCPP_ERROR(
      node_->get_logger(),
      "WaitForRobotReady: invalid scan_topic or timeout");
    return BT::NodeStatus::FAILURE;
  }

  {
    std::lock_guard<std::mutex> lock(mutex_);
    scan_received_ = false;
  }

  scan_subscription_ = node_->create_subscription<LaserScan>(
    scan_topic.value(),
    rclcpp::SensorDataQoS(),
    std::bind(
      &WaitForRobotReady::scanCallback,
      this,
      std::placeholders::_1));

  deadline_ = std::chrono::steady_clock::now() +
    std::chrono::duration_cast<std::chrono::steady_clock::duration>(
    std::chrono::duration<double>(timeout.value()));

  RCLCPP_INFO(
    node_->get_logger(),
    "WaitForRobotReady: waiting for scan on %s and map -> base TF",
    scan_topic.value().c_str());

  return checkReadiness();
}

BT::NodeStatus WaitForRobotReady::onRunning()
{
  return checkReadiness();
}

BT::NodeStatus WaitForRobotReady::checkReadiness()
{
  bool scan_received;
  {
    std::lock_guard<std::mutex> lock(mutex_);
    scan_received = scan_received_;
  }

  const auto map_frame = getInput<std::string>("map_frame");
  const auto base_frame = getInput<std::string>("base_frame");
  bool transform_available = false;

  if (map_frame && base_frame) {
    try {
      tf_buffer_->lookupTransform(
        map_frame.value(),
        base_frame.value(),
        tf2::TimePointZero);
      transform_available = true;
    } catch (const tf2::TransformException &) {
      transform_available = false;
    }
  }

  if (scan_received && transform_available) {
    RCLCPP_INFO(node_->get_logger(), "WaitForRobotReady: robot is ready");
    return BT::NodeStatus::SUCCESS;
  }

  if (std::chrono::steady_clock::now() >= deadline_) {
    RCLCPP_ERROR(
      node_->get_logger(),
      "WaitForRobotReady: timeout waiting for scan=%s, map_to_base_tf=%s",
      scan_received ? "ready" : "missing",
      transform_available ? "ready" : "missing");
    return BT::NodeStatus::FAILURE;
  }

  return BT::NodeStatus::RUNNING;
}

void WaitForRobotReady::onHalted()
{
  scan_subscription_.reset();
}

}  // namespace mobile_robot_bt
