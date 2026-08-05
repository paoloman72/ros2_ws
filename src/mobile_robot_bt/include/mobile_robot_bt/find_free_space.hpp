#pragma once

#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <utility>

#include "behaviortree_cpp/action_node.h"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"

namespace mobile_robot_bt
{

class FindFreeSpace : public BT::StatefulActionNode
{
public:
  FindFreeSpace(
    const std::string & name,
    const BT::NodeConfig & config);

  static BT::PortsList providedPorts();

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  using LaserScan = sensor_msgs::msg::LaserScan;

  void scanCallback(const LaserScan::SharedPtr scan);

  BT::NodeStatus tryCreateGoal();

  std::optional<std::pair<double, double>> findCandidate(
    const LaserScan & scan) const;

  std::optional<geometry_msgs::msg::PoseStamped> createGoal(
    double angle,
    double distance);

  static bool validRange(
    double value,
    const LaserScan & scan); 

  rclcpp::Node * node_{nullptr};

  rclcpp::Subscription<LaserScan>::SharedPtr scan_subscription_;

  std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;

  std::mutex scan_mutex_;
  LaserScan::SharedPtr latest_scan_;
};

}  // namespace mobile_robot_bt