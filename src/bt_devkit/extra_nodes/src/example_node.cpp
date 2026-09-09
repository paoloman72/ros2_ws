#include "bt_devkit/extra_nodes/example_node.hpp"

#include <stdexcept>

namespace bt_devkit
{

ExampleNode::ExampleNode(const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = config.blackboard->get<rclcpp::Node *>("node");
  if (node_ == nullptr) {
    throw std::runtime_error("ExampleNode: blackboard entry 'node' is missing");
  }
  // TODO: create LONG-LIVED interfaces here (action clients, tf2 buffers).
}

BT::PortsList ExampleNode::providedPorts()
{
  return {
    BT::InputPort<std::string>("message", "", "Example input port (edit me)"),
  };
}

BT::NodeStatus ExampleNode::onStart()
{
  // TODO: validate ports, reset per-tick state, kick off async work.
  const auto message = getInput<std::string>("message");
  RCLCPP_INFO(
    node_->get_logger(), "ExampleNode: started (message='%s')",
    message.has_value() ? message.value().c_str() : "");
  return BT::NodeStatus::SUCCESS;
}

BT::NodeStatus ExampleNode::onRunning()
{
  // TODO: read flags updated by ROS callbacks, return
  // RUNNING / SUCCESS / FAILURE.
  return BT::NodeStatus::SUCCESS;
}

void ExampleNode::onHalted()
{
  // TODO: cancel in-flight action goals (rule 5).
}

}  // namespace bt_devkit
