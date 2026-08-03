#include "mobile_robot_bt/generate_number.hpp"

#include <iostream>

namespace mobile_robot_bt
{

GenerateNumber::GenerateNumber(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::SyncActionNode(name, config)
{
}

BT::PortsList GenerateNumber::providedPorts()
{
  return {
    BT::OutputPort<int>("value")
  };
}

BT::NodeStatus GenerateNumber::tick()
{
  constexpr int generated_value = 42;

  setOutput("value", generated_value);

  std::cout
    << "GenerateNumber: wrote "
    << generated_value
    << " to output port 'value'"
    << std::endl;

  return BT::NodeStatus::SUCCESS;
}

}  // namespace mobile_robot_bt