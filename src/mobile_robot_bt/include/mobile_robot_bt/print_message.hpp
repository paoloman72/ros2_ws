#pragma once

#include <string>

#include "behaviortree_cpp/action_node.h"

namespace mobile_robot_bt
{

class PrintMessage : public BT::SyncActionNode
{
public:
  PrintMessage(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus tick() override;
};

}  // namespace mobile_robot_bt