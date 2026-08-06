#include "mobile_robot_bt/wait.hpp"

namespace mobile_robot_bt
{

Wait::Wait(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
}

BT::PortsList Wait::providedPorts()
{
  return {
    BT::InputPort<double>(
      "seconds",
      2.0,
      "Pause duration in seconds")
  };
}

BT::NodeStatus Wait::onStart()
{
  const auto seconds = getInput<double>("seconds");

  if (!seconds || seconds.value() < 0.0) {
    return BT::NodeStatus::FAILURE;
  }

  deadline_ =
    std::chrono::steady_clock::now() +
    std::chrono::duration_cast<std::chrono::steady_clock::duration>(
      std::chrono::duration<double>(seconds.value()));

  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus Wait::onRunning()
{
  if (std::chrono::steady_clock::now() >= deadline_) {
    return BT::NodeStatus::SUCCESS;
  }

  return BT::NodeStatus::RUNNING;
}

void Wait::onHalted()
{
  // Non serve cancellare nulla.
}

}  // namespace mobile_robot_bt