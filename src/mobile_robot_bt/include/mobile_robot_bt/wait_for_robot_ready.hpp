#pragma once

#include <chrono>
#include <memory>
#include <mutex>
#include <string>

#include "behaviortree_cpp/action_node.h"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"

namespace mobile_robot_bt
{

class WaitForRobotReady : public BT::StatefulActionNode
{
public:
  WaitForRobotReady(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  using LaserScan = sensor_msgs::msg::LaserScan;

  void scanCallback(const LaserScan::SharedPtr scan);
  BT::NodeStatus checkReadiness();

  rclcpp::Node * node_{nullptr};
  rclcpp::Subscription<LaserScan>::SharedPtr scan_subscription_;
  std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;

  std::mutex mutex_;
  bool scan_received_{false};
  std::chrono::steady_clock::time_point deadline_;
};

}  // namespace mobile_robot_bt
