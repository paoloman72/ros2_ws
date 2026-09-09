#include "behaviortree_cpp/bt_factory.h"

#include "bt_devkit/extra_nodes/register_extra_nodes.hpp"
#include "hello_mission/greet_node.hpp"

// This file produces the plugin entry point (createPlugin) that
// bt_executor loads. Keep it a SINGLE file: the executor loads exactly
// one plugin library per robot, so it must contain everything.
BT_REGISTER_NODES(factory)
{
  // Devkit scaffold nodes (ExampleNode skeleton + your extra nodes).
  bt_devkit::register_extra_nodes(factory);

  // Your custom nodes.
  factory.registerNodeType<hello_mission::GreetNode>("GreetNode");
}
