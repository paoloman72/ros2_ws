#pragma once

#include <memory>
#include <mutex>
#include <string>

#include "behaviortree_cpp/action_node.h"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "nav2_msgs/action/navigate_to_pose.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

namespace mobile_robot_bt
{

class NavigateToPose : public BT::StatefulActionNode
{
public:
  using Action = nav2_msgs::action::NavigateToPose;
  using GoalHandle = rclcpp_action::ClientGoalHandle<Action>;

  NavigateToPose(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  rclcpp::Node * node_{nullptr};
  rclcpp_action::Client<Action>::SharedPtr client_;
  GoalHandle::SharedPtr goal_handle_;

  std::mutex mutex_;
  bool goal_rejected_{false};
  bool result_received_{false};
  rclcpp_action::ResultCode result_code_{
    rclcpp_action::ResultCode::UNKNOWN};
  uint16_t nav2_error_code_{0};
  std::string nav2_error_message_;
};

}  // namespace mobile_robot_bt