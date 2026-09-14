#include "battery_check.hpp"

#include <cmath>
#include <functional>
#include <stdexcept>

namespace wander_mission
{

BatteryCheck::BatteryCheck(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = config.blackboard->get<rclcpp::Node *>("node");

  if (node_ == nullptr) {
    throw std::runtime_error(
            "BatteryCheck: blackboard entry 'node' is missing or null");
  }

  start_ = std::chrono::steady_clock::now();
}

BT::PortsList BatteryCheck::providedPorts()
{
  return {
    BT::InputPort<std::string>(
      "topic", "battery_state", "BatteryState topic to read"),
    BT::InputPort<int>(
      "threshold_percent", 30, "Low-battery threshold in percent"),
    BT::InputPort<bool>(
      "low", false,
      "true: succeed when the battery is at/below the threshold; "
      "false: succeed while the battery is above it"),
    BT::InputPort<double>(
      "timeout_sec", 10.0,
      "If no message arrives in time, assume healthy. 0 = wait forever"),
    BT::OutputPort<int>(
      "percent", "Last battery percentage (-1 if unknown)")
  };
}

void BatteryCheck::batteryCallback(const sensor_msgs::msg::BatteryState::SharedPtr msg)
{
  std::lock_guard<std::mutex> lock(mutex_);
  has_update_ = true;
  percent_ = msg->percentage;
}

BT::NodeStatus BatteryCheck::onStart()
{
  const auto topic = getInput<std::string>("topic");
  if (!topic || topic.value().empty()) {
    RCLCPP_ERROR(node_->get_logger(), "BatteryCheck: empty 'topic' input");
    return BT::NodeStatus::FAILURE;
  }
  subscription_ = node_->create_subscription<sensor_msgs::msg::BatteryState>(
    topic.value(), rclcpp::QoS(10),
    std::bind(&BatteryCheck::batteryCallback, this, std::placeholders::_1));
  RCLCPP_INFO(
    node_->get_logger(),
    "BatteryCheck: waiting for battery state on %s", topic.value().c_str());
  return check();
}

BT::NodeStatus BatteryCheck::onRunning()
{
  return check();
}

void BatteryCheck::onHalted()
{
}

BT::NodeStatus BatteryCheck::check()
{
  const auto threshold = getInput<int>("threshold_percent").value_or(30);
  const auto low = getInput<bool>("low").value_or(false);
  const auto timeout_sec = getInput<double>("timeout_sec").value_or(10.0);

  bool has_update = false;
  double percent = 0.0;
  {
    std::lock_guard<std::mutex> lock(mutex_);
    has_update = has_update_;
    if (has_update) {
      percent = percent_;
    }
  }

  if (has_update) {
    const bool is_low = percent <= static_cast<double>(threshold);
    setOutput("percent", static_cast<int>(std::lround(percent)));
    const bool condition_met = (low == is_low);
    RCLCPP_INFO(
      node_->get_logger(),
      "BatteryCheck: %.1f%% (threshold %d%%, low=%s) -> %s",
      percent, threshold, low ? "true" : "false",
      condition_met ? "SUCCESS" : "FAILURE");
    return condition_met ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
  }

  if (timeout_sec > 0.0 &&
    std::chrono::steady_clock::now() - start_ >=
    std::chrono::duration_cast<std::chrono::steady_clock::duration>(
      std::chrono::duration<double>(timeout_sec)))
  {
    setOutput("percent", -1);
    RCLCPP_WARN(
      node_->get_logger(),
      "BatteryCheck: no battery data within %.1fs, assuming healthy",
      timeout_sec);
    return low ? BT::NodeStatus::FAILURE : BT::NodeStatus::SUCCESS;
  }

  return BT::NodeStatus::RUNNING;
}

}  // namespace wander_mission