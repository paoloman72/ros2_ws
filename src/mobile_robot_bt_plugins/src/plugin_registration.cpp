#include "behaviortree_cpp/bt_factory.h"

#include "mobile_robot_bt_plugins/custom_hello.hpp"

#include "mobile_robot_bt/navigate_to_pose.hpp"
#include "mobile_robot_bt/find_free_space.hpp"
#include "mobile_robot_bt/wait_for_robot_ready.hpp"

BT_REGISTER_NODES(factory)
{
  factory.registerNodeType<
    mobile_robot_bt_plugins::CustomHello>(
      "CustomHello");

  factory.registerNodeType<
    mobile_robot_bt::NavigateToPose>(
      "NavigateToPose");

  factory.registerNodeType<
    mobile_robot_bt::FindFreeSpace>(
      "FindFreeSpace");

  factory.registerNodeType<
    mobile_robot_bt::WaitForRobotReady>(
      "WaitForRobotReady");
}