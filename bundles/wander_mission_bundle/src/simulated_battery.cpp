#include "simulated_battery.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace wander_mission
{

SimulatedBattery::SimulatedBattery(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = config.blackboard->get<rclcpp::Node *>("node");

  if (node_ == nullptr) {
    throw std::runtime_error(
            "SimulatedBattery: blackboard entry 'node' is missing or null");
  }

  start_ = std::chrono::steady_clock::now();
}

BT::PortsList SimulatedBattery::providedPorts()
{
  return {
    BT::InputPort<double>(
      "initial_percent", 100.0, "Starting battery level in percent"),
    BT::InputPort<double>(
      "drain_per_sec", 0.5, "Drain rate in percent per second"),
    BT::InputPort<int>(
      "threshold_percent", 30, "Low-battery threshold in percent"),
    BT::InputPort<bool>(
      "low", false,
      "true: succeed when the battery is at/below the threshold; "
      "false: succeed while the battery is above it"),
    BT::OutputPort<int>(
      "percent", "Current simulated battery percentage")
  };
}

BT::NodeStatus SimulatedBattery::onStart()
{
  // Log the (continuous) drain origin only on the very first start. The node
  // is restarted on every Repeat cycle, but start_ (set in the constructor, at
  // tree-build time) is NOT reset, so the level keeps dropping across the whole
  // mission - mirroring the standalone battery_simulator's continuous drain.
  if (!start_logged_) {
    start_logged_ = true;
    RCLCPP_INFO(
      node_->get_logger(),
      "SimulatedBattery: sim started (initial %.1f%%, drain %.2f%%/s, threshold %d%%)",
      getInput<double>("initial_percent").value_or(100.0),
      getInput<double>("drain_per_sec").value_or(0.5),
      getInput<int>("threshold_percent").value_or(30));
  }
  return check();
}

BT::NodeStatus SimulatedBattery::onRunning()
{
  return check();
}

void SimulatedBattery::onHalted()
{
}

BT::NodeStatus SimulatedBattery::check()
{
  const auto initial = getInput<double>("initial_percent").value_or(100.0);
  const auto drain = getInput<double>("drain_per_sec").value_or(0.5);
  const auto threshold = getInput<int>("threshold_percent").value_or(30);
  const auto low = getInput<bool>("low").value_or(false);

  const double elapsed =
    std::chrono::duration<double>(
      std::chrono::steady_clock::now() - start_).count();
  const double percent = std::max(0.0, initial - drain * elapsed);
  const int rounded = static_cast<int>(std::lround(percent));

  setOutput("percent", rounded);

  // Log only when the integer level changes (avoids 10 Hz spam).
  if (rounded != last_logged_percent_) {
    last_logged_percent_ = rounded;
    RCLCPP_INFO(
      node_->get_logger(),
      "SimulatedBattery: %d%% (threshold %d%%, low=%s)",
      rounded, threshold, low ? "true" : "false");
  }

  const bool is_low = percent <= static_cast<double>(threshold);
  const bool condition_met = (low == is_low);
  return condition_met ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
}

}  // namespace wander_mission
