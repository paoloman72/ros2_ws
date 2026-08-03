#include "mobile_robot_bt/print_message.hpp"

#include <iostream>

namespace mobile_robot_bt
{

PrintMessage::PrintMessage(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::SyncActionNode(name, config)
{
}

BT::PortsList PrintMessage::providedPorts()
{
  return {
    BT::InputPort<std::string>("message")
  };
}

BT::NodeStatus PrintMessage::tick()
{
  const auto message = getInput<std::string>("message");

  if (!message) {
    std::cerr
      << "PrintMessage: missing input port 'message': "
      << message.error()
      << std::endl;

    return BT::NodeStatus::FAILURE;
  }

  std::cout
    << "PrintMessage: "
    << message.value()
    << std::endl;

  return BT::NodeStatus::SUCCESS;
}

}  // namespace mobile_robot_bt