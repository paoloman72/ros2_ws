#pragma once

#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"

namespace mobile_robot_bt
{

class RosLog : public BT::SyncActionNode
{
public:
  RosLog(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus tick() override;

private:
  rclcpp::Node * node_{nullptr};
};

}  // namespace mobile_robot_bt