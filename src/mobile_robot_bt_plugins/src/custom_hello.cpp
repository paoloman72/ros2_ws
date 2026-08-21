#include "mobile_robot_bt_plugins/custom_hello.hpp"

#include <iostream>

namespace mobile_robot_bt_plugins
{

CustomHello::CustomHello(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::SyncActionNode(name, config)
{
}

BT::PortsList CustomHello::providedPorts()
{
  return {
    BT::InputPort<std::string>(
      "message",
      "Hello from plugin",
      "Message to print")
  };
}

BT::NodeStatus CustomHello::tick()
{
  const auto message = getInput<std::string>("message");

  if (!message) {
    return BT::NodeStatus::FAILURE;
  }

  std::cout
    << "[PLUGIN] "
    << message.value()
    << std::endl;

  return BT::NodeStatus::SUCCESS;
}

}  // namespace mobile_robot_bt_plugins