#include "mobile_robot_bt/create_pose.hpp"

#include <cmath>
#include <iostream>

namespace mobile_robot_bt
{

CreatePose::CreatePose(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::SyncActionNode(name, config)
{
}

BT::PortsList CreatePose::providedPorts()
{
  return {
    BT::InputPort<double>("x"),
    BT::InputPort<double>("y"),
    BT::InputPort<double>("yaw"),
    BT::InputPort<std::string>("frame_id", "map"),
    BT::OutputPort<geometry_msgs::msg::PoseStamped>("pose")
  };
}

BT::NodeStatus CreatePose::tick()
{
  const auto x = getInput<double>("x");
  const auto y = getInput<double>("y");
  const auto yaw = getInput<double>("yaw");
  const auto frame_id = getInput<std::string>("frame_id");

  if (!x || !y || !yaw || !frame_id) {
    std::cerr << "CreatePose: missing or invalid input port" << std::endl;
    return BT::NodeStatus::FAILURE;
  }

  geometry_msgs::msg::PoseStamped pose;
  pose.header.frame_id = frame_id.value();

  pose.pose.position.x = x.value();
  pose.pose.position.y = y.value();
  pose.pose.position.z = 0.0;

  pose.pose.orientation.z = std::sin(yaw.value() / 2.0);
  pose.pose.orientation.w = std::cos(yaw.value() / 2.0);

  setOutput("pose", pose);

  std::cout
    << "CreatePose: x=" << x.value()
    << ", y=" << y.value()
    << ", yaw=" << yaw.value()
    << ", frame=" << frame_id.value()
    << std::endl;

  return BT::NodeStatus::SUCCESS;
}

}  // namespace mobile_robot_bt