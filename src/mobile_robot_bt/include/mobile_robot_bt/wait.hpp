#pragma once

#include <chrono>
#include <string>

#include "behaviortree_cpp/action_node.h"

namespace mobile_robot_bt
{

class Wait : public BT::StatefulActionNode
{
public:
  Wait(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  std::chrono::steady_clock::time_point deadline_;
};

}  // namespace mobile_robot_bt