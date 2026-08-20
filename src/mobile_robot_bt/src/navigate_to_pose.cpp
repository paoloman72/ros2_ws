#include "mobile_robot_bt/navigate_to_pose.hpp"

#include <chrono>
#include <stdexcept>

using namespace std::chrono_literals;

namespace mobile_robot_bt
{

NavigateToPose::NavigateToPose(
  const std::string & name,
  const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = config.blackboard->get<rclcpp::Node *>("node");

  if (node_ == nullptr) {
    throw std::runtime_error(
      "NavigateToPose: blackboard entry 'node' is missing or null");
  }

  const auto robot_namespace =
    config.blackboard->get<std::string>(
      "robot_namespace");

  const std::string action_name =
    robot_namespace.empty()
    ? "/navigate_to_pose"
    : robot_namespace + "/navigate_to_pose";

  client_ = rclcpp_action::create_client<Action>(
    node_,
    action_name);
}

BT::PortsList NavigateToPose::providedPorts()
{
  return {
    BT::InputPort<geometry_msgs::msg::PoseStamped>("pose")
  };
}

BT::NodeStatus NavigateToPose::onStart()
{
  auto pose = getInput<geometry_msgs::msg::PoseStamped>("pose");

  if (!pose) {
    RCLCPP_ERROR(
      node_->get_logger(),
      "NavigateToPose: missing input port 'pose': %s",
      pose.error().c_str());

    return BT::NodeStatus::FAILURE;
  }

  if (!client_->wait_for_action_server(2s)) {
    RCLCPP_ERROR(
      node_->get_logger(),
      "NavigateToPose action server is unavailable");

    return BT::NodeStatus::FAILURE;
  }

  {
    std::lock_guard<std::mutex> lock(mutex_);

    goal_handle_.reset();
    goal_rejected_ = false;
    result_received_ = false;
    result_code_ = rclcpp_action::ResultCode::UNKNOWN;
    nav2_error_code_ = 0;
    nav2_error_message_.clear();
  }

  Action::Goal goal;
  goal.pose = pose.value();

  // Usa il clock ROS del MissionExecutor, quindi anche /clock in simulazione.
  goal.pose.header.stamp = node_->now();

  // Stringa vuota: Nav2 usa il proprio BT configurato.
  goal.behavior_tree = "";

  rclcpp_action::Client<Action>::SendGoalOptions options;

  options.goal_response_callback =
    [this](const GoalHandle::SharedPtr & goal_handle)
    {
      std::lock_guard<std::mutex> lock(mutex_);

      if (!goal_handle) {
        goal_rejected_ = true;

        RCLCPP_ERROR(
          node_->get_logger(),
          "NavigateToPose: goal rejected");
        return;
      }

      goal_handle_ = goal_handle;

      RCLCPP_INFO(
        node_->get_logger(),
        "NavigateToPose: goal accepted");
    };

  options.feedback_callback =
    [this](
      GoalHandle::SharedPtr,
      const std::shared_ptr<const Action::Feedback> feedback)
    {
      RCLCPP_DEBUG(
        node_->get_logger(),
        "NavigateToPose: %.2f m remaining, %d recoveries",
        feedback->distance_remaining,
        feedback->number_of_recoveries);
    };

  options.result_callback =
    [this](const GoalHandle::WrappedResult & wrapped_result)
    {
      std::lock_guard<std::mutex> lock(mutex_);

      result_code_ = wrapped_result.code;
      result_received_ = true;

      if (wrapped_result.result) {
        nav2_error_code_ = wrapped_result.result->error_code;
        nav2_error_message_ = wrapped_result.result->error_msg;
      }
    };

  client_->async_send_goal(goal, options);

  RCLCPP_INFO(
    node_->get_logger(),
    "NavigateToPose: sending goal x=%.2f, y=%.2f",
    goal.pose.pose.position.x,
    goal.pose.pose.position.y);

  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus NavigateToPose::onRunning()
{
  std::lock_guard<std::mutex> lock(mutex_);

  if (goal_rejected_) {
    return BT::NodeStatus::FAILURE;
  }

  if (!result_received_) {
    return BT::NodeStatus::RUNNING;
  }

  if (
    result_code_ == rclcpp_action::ResultCode::SUCCEEDED &&
    nav2_error_code_ == Action::Result::NONE)
  {
    RCLCPP_INFO(
      node_->get_logger(),
      "NavigateToPose: destination reached");

    return BT::NodeStatus::SUCCESS;
  }

  RCLCPP_ERROR(
    node_->get_logger(),
    "NavigateToPose failed: result_code=%d, error_code=%u, message='%s'",
    static_cast<int>(result_code_),
    nav2_error_code_,
    nav2_error_message_.c_str());

  return BT::NodeStatus::FAILURE;
}

void NavigateToPose::onHalted()
{
  std::lock_guard<std::mutex> lock(mutex_);

  if (goal_handle_ && !result_received_) {
    RCLCPP_WARN(
      node_->get_logger(),
      "NavigateToPose halted: canceling active goal");

    client_->async_cancel_goal(goal_handle_);
  }
}

}  // namespace mobile_robot_bt