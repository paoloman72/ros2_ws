#include "behaviortree_cpp/bt_factory.h"

#include "mobile_robot_bt_plugins/custom_hello.hpp"

BT_REGISTER_NODES(factory)
{
  factory.registerNodeType<
    mobile_robot_bt_plugins::CustomHello>(
      "CustomHello");
}