#include "behaviortree_cpp/bt_factory.h"

#include "battery_check.hpp"
#include "bt_devkit/extra_nodes/register_extra_nodes.hpp"
#include "create_pose.hpp"
#include "find_free_space.hpp"
#include "navigate_to_pose.hpp"
#include "pick_random_pose.hpp"
#include "wait_for_robot_ready.hpp"

// This file produces the plugin entry point (createPlugin) that
// bt_executor loads. Keep it a SINGLE file: the executor loads exactly
// one plugin library per robot, so it must contain everything.
BT_REGISTER_NODES(factory)
{
  // Devkit scaffold nodes (ExampleNode skeleton + your extra nodes).
  bt_devkit::register_extra_nodes(factory);

  // Your custom nodes.
  factory.registerNodeType<wander_mission::BatteryCheck>("BatteryCheck");
  factory.registerNodeType<wander_mission::PickRandomPose>("PickRandomPose");

  // Vendored navigation nodes (Flow B; class names as in the
  // reference bundle).
  factory.registerNodeType<mobile_robot_bt::CreatePose>("CreatePose");
  factory.registerNodeType<mobile_robot_bt::FindFreeSpace>("FindFreeSpace");
  factory.registerNodeType<mobile_robot_bt::NavigateToPose>("NavigateToPose");
  factory.registerNodeType<mobile_robot_bt::WaitForRobotReady>("WaitForRobotReady");
}
