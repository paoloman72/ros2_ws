#pragma once

#include <string>

#include "behaviortree_cpp/action_node.h"
#include "geometry_msgs/msg/pose_stamped.hpp"

namespace mobile_robot_bt
{

class CreatePose : public BT::SyncActionNode
{
public:
  CreatePose(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus tick() override;
};

}  // namespace mobile_robot_bt