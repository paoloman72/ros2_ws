#pragma once

#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"

namespace mobile_robot_bt_plugins
{

class CustomHello : public BT::SyncActionNode
{
public:
  CustomHello(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus tick() override;
};

}  // namespace mobile_robot_bt_plugins