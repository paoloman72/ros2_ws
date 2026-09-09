// bt_devkit -- extra nodes scaffold
//
// ExampleNode is the devkit's starting template for a STATEFUL action node
// (work spanning multiple ticks: action clients, waiting for data, services).
//
// How to use:
//   1. Copy example_node.hpp/.cpp into your project and rename.
//   2. Declare your ports in providedPorts().
//   3. Implement the logic (5 authoring rules: BT_MISSION_DEVELOPMENT_GUIDE.md,
//      section 3).
//   4. Register it (see register_extra_nodes.cpp / your register_nodes.cpp).

#pragma once

#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"

namespace bt_devkit
{

class ExampleNode : public BT::StatefulActionNode
{
public:
  ExampleNode(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  // Injected by bt_executor via the blackboard key "node".
  // Rule 1: never create your own node, always use this one.
  rclcpp::Node * node_{nullptr};
};

}  // namespace bt_devkit
