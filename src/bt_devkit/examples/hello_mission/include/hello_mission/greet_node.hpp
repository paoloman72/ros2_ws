#pragma once

#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"

namespace hello_mission
{

// Minimal custom node: proves your project compiles, registers and runs
// with the devkit executor. Replace it with your real nodes.
//
// Template for a STATEFUL node (multi-tick work):
// bt_devkit/extra_nodes/include/bt_devkit/extra_nodes/example_node.hpp

class GreetNode : public BT::SyncActionNode
{
public:
  GreetNode(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus tick() override;

private:
  // Injected by bt_executor via the blackboard key "node".
  rclcpp::Node * node_{nullptr};
};

}  // namespace hello_mission
