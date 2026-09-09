#include "hello_mission/greet_node.hpp"

#include <stdexcept>

namespace hello_mission
{

GreetNode::GreetNode(const std::string & name, const BT::NodeConfig & config)
: BT::SyncActionNode(name, config)
{
  node_ = config.blackboard->get<rclcpp::Node *>("node");
  if (node_ == nullptr) {
    throw std::runtime_error("GreetNode: blackboard entry 'node' is missing");
  }
}

BT::PortsList GreetNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("who", "world", "Who to greet"),
    // BT.CPP v4: output ports are blackboard-backed. The default must be a
    // blackboard key in '{...}' syntax (the reference bundle uses e.g.
    // OutputPort<int>("value") and connects value="{shared_number}" in the
    // tree). Here the default key "{greeting}" is used, so the tree does not
    // need to connect the port; setOutput() writes to it.
    BT::OutputPort<std::string>("greeting", "{greeting}", "The greeting text"),
  };
}

BT::NodeStatus GreetNode::tick()
{
  const auto who = getInput<std::string>("who");
  const std::string greeting = "Hello, " + (who.has_value() ? who.value() : "world") + "!";
  setOutput<std::string>("greeting", greeting);
  RCLCPP_INFO(node_->get_logger(), "%s", greeting.c_str());
  return BT::NodeStatus::SUCCESS;
}

}  // namespace hello_mission
