#include "mobile_robot_bt/print_number.hpp"

#include <iostream>

namespace mobile_robot_bt
{

PrintNumber::PrintNumber(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::SyncActionNode(name, config)
{
}

BT::PortsList PrintNumber::providedPorts()
{
  return {
    BT::InputPort<int>("value")
  };
}

BT::NodeStatus PrintNumber::tick()
{
  const auto value = getInput<int>("value");

  if (!value) {
    std::cerr
      << "PrintNumber: missing input port 'value': "
      << value.error()
      << std::endl;

    return BT::NodeStatus::FAILURE;
  }

  std::cout
    << "PrintNumber: read "
    << value.value()
    << " from input port 'value'"
    << std::endl;

  return BT::NodeStatus::SUCCESS;
}

}  // namespace mobile_robot_bt