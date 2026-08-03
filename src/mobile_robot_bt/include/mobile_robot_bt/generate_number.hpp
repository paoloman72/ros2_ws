#pragma once

#include <string>

#include "behaviortree_cpp/action_node.h"

namespace mobile_robot_bt
{

class GenerateNumber : public BT::SyncActionNode
{
public:
  GenerateNumber(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus tick() override;
};

}  // namespace mobile_robot_bt