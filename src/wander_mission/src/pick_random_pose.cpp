#include "pick_random_pose.hpp"

#include <random>

namespace wander_mission
{

PickRandomPose::PickRandomPose(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::SyncActionNode(name, config), rng_(std::random_device{}())
{
  // Optional: used for logging when running under bt_executor.
  node_ = config.blackboard->get<rclcpp::Node *>("node");
}

BT::PortsList PickRandomPose::providedPorts()
{
  return {
    BT::InputPort<double>("min_x", -2.0, "Minimum x (m)"),
    BT::InputPort<double>("max_x", 2.0, "Maximum x (m)"),
    BT::InputPort<double>("min_y", -2.0, "Minimum y (m)"),
    BT::InputPort<double>("max_y", 2.0, "Maximum y (m)"),
    BT::OutputPort<double>("x", "Random x coordinate (m)"),
    BT::OutputPort<double>("y", "Random y coordinate (m)")
  };
}

BT::NodeStatus PickRandomPose::tick()
{
  const auto min_x = getInput<double>("min_x");
  const auto max_x = getInput<double>("max_x");
  const auto min_y = getInput<double>("min_y");
  const auto max_y = getInput<double>("max_y");

  if (!min_x || !max_x || !min_y || !max_y ||
    max_x.value() <= min_x.value() || max_y.value() <= min_y.value())
  {
    return BT::NodeStatus::FAILURE;
  }

  std::uniform_real_distribution<double> dist_x(min_x.value(), max_x.value());
  std::uniform_real_distribution<double> dist_y(min_y.value(), max_y.value());
  const auto x = dist_x(rng_);
  const auto y = dist_y(rng_);

  setOutput("x", x);
  setOutput("y", y);

  if (node_ != nullptr) {
    RCLCPP_INFO(node_->get_logger(), "PickRandomPose: (%.2f, %.2f)", x, y);
  }
  return BT::NodeStatus::SUCCESS;
}

}  // namespace wander_mission