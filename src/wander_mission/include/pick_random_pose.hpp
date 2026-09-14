#pragma once

#include <random>
#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"

namespace wander_mission
{

/// Outputs a random point (x, y) inside the axis-aligned box
/// [min_x, max_x] x [min_y, max_y]. The point is redrawn on every tick,
/// so inside a Repeat loop it yields a fresh waypoint each cycle.
///
/// If the rclcpp::Node injected by bt_executor is present on the
/// blackboard entry "node", it is used for logging (optional).
class PickRandomPose : public BT::SyncActionNode
{
public:
  PickRandomPose(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus tick() override;

private:
  std::mt19937 rng_;
  rclcpp::Node * node_{nullptr};
};

}  // namespace wander_mission