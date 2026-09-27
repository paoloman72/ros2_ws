#pragma once

#include <chrono>
#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"

namespace wander_mission
{

/// Simulates a battery draining at a constant rate, for local testing in
/// the Gazebo simulator (which has no real battery driver).
///
/// Drop-in replacement for the external `battery_simulator` node: the level
/// is computed internally from elapsed wall-clock time instead of reading a
/// sensor_msgs/BatteryState topic. On a real robot, use `BatteryCheck`
/// (topic-based) instead - the only tree change is the node name.
///
/// Returns the same contract as `BatteryCheck`:
///   low=true  -> SUCCESS when the battery is low,  FAILURE otherwise
///   low=false -> SUCCESS while the battery is OK,  FAILURE when low
///
/// StatefulActionNode: the level is recomputed on every tick. Uses the
/// rclcpp::Node injected by bt_executor on the blackboard entry "node".
class SimulatedBattery : public BT::StatefulActionNode
{
public:
  SimulatedBattery(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  BT::NodeStatus check();

  rclcpp::Node * node_{nullptr};
  std::chrono::steady_clock::time_point start_;
  int last_logged_percent_{-1000};
  bool start_logged_{false};
};

}  // namespace wander_mission
