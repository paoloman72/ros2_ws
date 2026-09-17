#pragma once

#include <chrono>
#include <memory>
#include <mutex>
#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/battery_state.hpp"

namespace wander_mission
{

/// Waits for a sensor_msgs/BatteryState message on `topic`, then reports
/// whether the battery is low (at or below `threshold_percent`).
///
///   low=true  -> SUCCESS when the battery is low,  FAILURE otherwise
///   low=false -> SUCCESS while the battery is OK,  FAILURE when low
///
/// If no message arrives within `timeout_sec` (> 0), the battery is
/// assumed healthy (not low), so a missing battery driver cannot wedge
/// the tree. timeout_sec = 0 means: wait forever.
///
/// StatefulActionNode (not SyncActionNode): the wait for the first
/// battery message spans multiple ticks. Uses the rclcpp::Node injected
/// by bt_executor on the blackboard entry "node" (same contract as the
/// vendored navigation nodes).
class BatteryCheck : public BT::StatefulActionNode
{
public:
  BatteryCheck(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  BT::NodeStatus check();
  void batteryCallback(const sensor_msgs::msg::BatteryState::SharedPtr msg);

  rclcpp::Node * node_{nullptr};
  rclcpp::Subscription<sensor_msgs::msg::BatteryState>::SharedPtr subscription_;

  std::mutex mutex_;
  bool has_update_{false};
  double percent_{0.0};
  std::chrono::steady_clock::time_point start_;
};

}  // namespace wander_mission