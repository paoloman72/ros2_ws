#include "mobile_robot_bt/ros_log.hpp"

#include <stdexcept>

namespace mobile_robot_bt
{

RosLog::RosLog(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::SyncActionNode(name, config)
{
  node_ = config.blackboard->get<rclcpp::Node *>("node");

  if (node_ == nullptr) {
    throw std::runtime_error(
      "RosLog: blackboard entry 'node' is null");
  }
}

BT::PortsList RosLog::providedPorts()
{
  return {
    BT::InputPort<std::string>("message")
  };
}

BT::NodeStatus RosLog::tick()
{
  const auto message = getInput<std::string>("message");

  if (!message) {
    RCLCPP_ERROR(
      node_->get_logger(),
      "RosLog: missing input port 'message': %s",
      message.error().c_str());

    return BT::NodeStatus::FAILURE;
  }

  RCLCPP_INFO(
    node_->get_logger(),
    "RosLog: %s",
    message.value().c_str());

  return BT::NodeStatus::SUCCESS;
}

}  // namespace mobile_robot_bt