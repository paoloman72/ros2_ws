#include <chrono>
#include <memory>
#include <string>

#include "behaviortree_cpp/bt_factory.h"
#include "rclcpp/rclcpp.hpp"
#include "mobile_robot_bt/print_message.hpp"
#include "mobile_robot_bt/generate_number.hpp"
#include "mobile_robot_bt/print_number.hpp"
#include "mobile_robot_bt/ros_log.hpp"
#include "mobile_robot_bt/create_pose.hpp"
#include "mobile_robot_bt/navigate_to_pose.hpp"
#include "mobile_robot_bt/find_free_space.hpp"
#include "mobile_robot_bt/wait_for_robot_ready.hpp"
#include "behaviortree_cpp/loggers/groot2_publisher.h"
#include "mobile_robot_bt/wait.hpp"

using namespace std::chrono_literals;

class MissionExecutor : public rclcpp::Node
{
public:
  MissionExecutor()
  : Node("mission_executor")
  {
    declare_parameter<std::string>("bt_xml", "");
    declare_parameter<int>("groot_port", 1669);

    const auto bt_xml = get_parameter("bt_xml").as_string();
    const auto groot_port = static_cast<uint16_t>(get_parameter("groot_port").as_int());

    if (bt_xml.empty()) {
      throw std::runtime_error(
        "Parameter 'bt_xml' is empty. Pass the full path to a BT XML file.");
    }

    RCLCPP_INFO(
      get_logger(),
      "Loading Behavior Tree from: %s",
      bt_xml.c_str());

    factory_.registerNodeType<mobile_robot_bt::PrintMessage>(
        "PrintMessage");

    factory_.registerNodeType<mobile_robot_bt::GenerateNumber>(
        "GenerateNumber");

    factory_.registerNodeType<mobile_robot_bt::PrintNumber>(
        "PrintNumber");

    factory_.registerNodeType<mobile_robot_bt::RosLog>(
        "RosLog");

    factory_.registerNodeType<mobile_robot_bt::CreatePose>(
        "CreatePose");

    factory_.registerNodeType<mobile_robot_bt::NavigateToPose>(
        "NavigateToPose");

    factory_.registerNodeType<mobile_robot_bt::FindFreeSpace>(
        "FindFreeSpace");

    factory_.registerNodeType<mobile_robot_bt::Wait>(
        "Wait");        

    factory_.registerNodeType<mobile_robot_bt::WaitForRobotReady>(
      "WaitForRobotReady");
        
    declare_parameter<std::string>("robot_namespace", "");

    const auto robot_namespace =
      get_parameter("robot_namespace").as_string();

    blackboard_ = BT::Blackboard::create();
    blackboard_->set<rclcpp::Node *>("node", this);
    blackboard_->set<std::string>(
      "robot_namespace",
      robot_namespace);

    tree_ = factory_.createTreeFromFile(
        bt_xml,
        blackboard_);

    groot_publisher_ =
      std::make_unique<BT::Groot2Publisher>(tree_, groot_port);

    timer_ = create_wall_timer(
      100ms,
      std::bind(&MissionExecutor::tickTree, this));
  }

private:
  void tickTree()
  {
    const auto status = tree_.tickOnce();

    if (status == BT::NodeStatus::SUCCESS) {
      RCLCPP_INFO(get_logger(), "Mission completed successfully.");
      timer_->cancel();
    } else if (status == BT::NodeStatus::FAILURE) {
      RCLCPP_ERROR(get_logger(), "Mission failed.");
      timer_->cancel();
    }
  }

  BT::BehaviorTreeFactory factory_;
  BT::Tree tree_;
  rclcpp::TimerBase::SharedPtr timer_;
  BT::Blackboard::Ptr blackboard_;
  std::unique_ptr<BT::Groot2Publisher> groot_publisher_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  try {
    auto node = std::make_shared<MissionExecutor>();
    rclcpp::spin(node);
  } catch (const std::exception & error) {
    RCLCPP_FATAL(
      rclcpp::get_logger("mission_executor"),
      "Fatal error: %s",
      error.what());
  }

  rclcpp::shutdown();
  return 0;
}