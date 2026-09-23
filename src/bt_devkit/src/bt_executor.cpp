#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>

#include "behaviortree_cpp/bt_factory.h"
#include "behaviortree_cpp/loggers/groot2_publisher.h"
#include "rclcpp/rclcpp.hpp"

namespace
{

using namespace std::chrono_literals;

void write_ready_file(const std::string & path_string)
{
  if (path_string.empty()) {
    return;
  }

  const std::filesystem::path path(path_string);
  if (path.has_parent_path()) {
    std::filesystem::create_directories(path.parent_path());
  }

  const auto temporary = path.string() + ".tmp";
  {
    std::ofstream stream(temporary, std::ios::out | std::ios::trunc);
    if (!stream) {
      throw std::runtime_error("Cannot create ready file: " + temporary);
    }
    stream << "ready\n";
  }

  std::error_code error;
  std::filesystem::rename(temporary, path, error);
  if (error) {
    std::filesystem::remove(path, error);
    error.clear();
    std::filesystem::rename(temporary, path, error);
  }
  if (error) {
    throw std::runtime_error(
            "Cannot publish ready file '" + path.string() + "': " + error.message());
  }
}

class BtExecutor : public rclcpp::Node
{
public:
  BtExecutor()
  : Node("bt_executor")
  {
    declare_parameter<std::string>("bt_xml", "");
    declare_parameter<std::string>("plugin_library", "");
    declare_parameter<int>("tick_period_ms", 100);
    declare_parameter<bool>("groot_enabled", false);
    declare_parameter<int>("groot_port", 1669);
    declare_parameter<std::string>("ready_file", "");
    declare_parameter<std::string>("start_file", "");

    bt_xml_ = get_parameter("bt_xml").as_string();
    plugin_library_ = get_parameter("plugin_library").as_string();
    ready_file_ = get_parameter("ready_file").as_string();
    start_file_ = get_parameter("start_file").as_string();

    const auto tick_period_ms = get_parameter("tick_period_ms").as_int();
    if (tick_period_ms <= 0) {
      throw std::runtime_error("Parameter 'tick_period_ms' must be greater than zero");
    }
    tick_period_ = std::chrono::milliseconds(tick_period_ms);

    if (bt_xml_.empty()) {
      throw std::runtime_error("Parameter 'bt_xml' is empty");
    }
    if (plugin_library_.empty()) {
      throw std::runtime_error("Parameter 'plugin_library' is empty");
    }

    const std::filesystem::path tree_path(bt_xml_);
    const std::filesystem::path plugin_path(plugin_library_);
    if (!std::filesystem::is_regular_file(tree_path)) {
      throw std::runtime_error("Behavior Tree XML does not exist: " + bt_xml_);
    }
    if (!std::filesystem::is_regular_file(plugin_path)) {
      throw std::runtime_error("Behavior Tree plugin does not exist: " + plugin_library_);
    }

    RCLCPP_INFO(get_logger(), "Loading Behavior Tree plugin: %s", plugin_library_.c_str());
    factory_.registerFromPlugin(plugin_library_);

    blackboard_ = BT::Blackboard::create();
    // Existing custom nodes use this blackboard entry to create ROS publishers,
    // subscriptions and action clients in the executor's robot namespace.
    blackboard_->set<rclcpp::Node *>("node", this);

    RCLCPP_INFO(get_logger(), "Loading Behavior Tree XML: %s", bt_xml_.c_str());
    tree_ = factory_.createTreeFromFile(bt_xml_, blackboard_);

    if (get_parameter("groot_enabled").as_bool()) {
      const auto port = get_parameter("groot_port").as_int();
      if (port <= 0 || port > 65535) {
        throw std::runtime_error("Parameter 'groot_port' must be in range 1..65535");
      }
      groot_publisher_ = std::make_unique<BT::Groot2Publisher>(
        tree_, static_cast<uint16_t>(port));
      RCLCPP_INFO(get_logger(), "Groot2 publisher enabled on port %ld", port);
    }
  }

  int run()
  {
    rclcpp::executors::SingleThreadedExecutor executor;
    executor.add_node(shared_from_this());

    write_ready_file(ready_file_);
    RCLCPP_INFO(get_logger(), "Behavior Tree executor ready");

    if (!start_file_.empty()) {
      RCLCPP_INFO(get_logger(), "Waiting for start barrier: %s", start_file_.c_str());
      while (rclcpp::ok() && !std::filesystem::exists(start_file_)) {
        executor.spin_some();
        std::this_thread::sleep_for(20ms);
      }
    }

    if (!rclcpp::ok()) {
      halt_tree_noexcept();
      return 130;
    }

    RCLCPP_INFO(get_logger(), "Starting Behavior Tree ticks");

    while (rclcpp::ok()) {
      // Process ROS callbacks before and after every tick. Stateful BT nodes can
      // therefore consume action/subscription callbacks without owning executors.
      executor.spin_some();

      BT::NodeStatus status = BT::NodeStatus::IDLE;
      try {
        status = tree_.tickOnce();
      } catch (const std::exception & error) {
        RCLCPP_ERROR(get_logger(), "Behavior Tree tick threw an exception: %s", error.what());
        write_tick_progress("ERROR", true);
        halt_tree_noexcept();
        return 2;
      }

      executor.spin_some();

      // Observed by bt_mission_launcher. Only the actual tick loop updates this
      // counter: a blocked tick/callback must not look like a healthy executor.
      ++completed_ticks_;

      if (status == BT::NodeStatus::SUCCESS) {
        RCLCPP_INFO(get_logger(), "Behavior Tree completed with SUCCESS");
        halt_tree_noexcept();
        write_tick_progress("SUCCESS", true);
        return 0;
      }
      if (status == BT::NodeStatus::FAILURE) {
        RCLCPP_ERROR(get_logger(), "Behavior Tree completed with FAILURE");
        write_tick_progress("FAILURE", true);
        halt_tree_noexcept();
        return 1;
      }
      if (status != BT::NodeStatus::RUNNING) {
        RCLCPP_ERROR(
          get_logger(), "Behavior Tree returned unexpected status code: %d",
          static_cast<int>(status));
        write_tick_progress("ERROR", true);
        halt_tree_noexcept();
        return 3;
      }

      write_tick_progress("RUNNING");
      std::this_thread::sleep_for(tick_period_);
    }

    halt_tree_noexcept();
    return 130;
  }

private:
  void write_tick_progress(const char * status, bool force = false)
  {
    // Keep the launcher CLI and every mission bundle unchanged. The existing
    // per-run, per-robot ready path also identifies its progress sidecar.
    if (ready_file_.empty()) {
      return;
    }
    const auto now = std::chrono::steady_clock::now();
    if (!force && tick_progress_written_ && now - last_tick_write_ < 1s) {
      return;
    }
    const std::string path = ready_file_ + ".ticks";
    const std::string temporary = path + ".tmp";
    {
      std::ofstream stream(temporary, std::ios::out | std::ios::trunc);
      stream << completed_ticks_ << " " << status << "\n";
      stream.flush();
      if (!stream) {
        throw std::runtime_error("Cannot write BT tick progress: " + temporary);
      }
    }
    std::filesystem::rename(temporary, path);
    last_tick_write_ = now;
    tick_progress_written_ = true;
  }

  std::uint64_t completed_ticks_{0};
  std::chrono::steady_clock::time_point last_tick_write_{};
  bool tick_progress_written_{false};

  void halt_tree_noexcept() noexcept
  {
    try {
      tree_.haltTree();
    } catch (const std::exception & error) {
      RCLCPP_WARN(get_logger(), "Exception while halting Behavior Tree: %s", error.what());
    } catch (...) {
      RCLCPP_WARN(get_logger(), "Unknown exception while halting Behavior Tree");
    }
  }

  std::string bt_xml_;
  std::string plugin_library_;
  std::string ready_file_;
  std::string start_file_;
  std::chrono::milliseconds tick_period_{100};

  BT::BehaviorTreeFactory factory_;
  BT::Blackboard::Ptr blackboard_;
  BT::Tree tree_;
  std::unique_ptr<BT::Groot2Publisher> groot_publisher_;
};

}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  int return_code = 2;

  try {
    auto node = std::make_shared<BtExecutor>();
    return_code = node->run();
  } catch (const std::exception & error) {
    RCLCPP_FATAL(rclcpp::get_logger("bt_executor"), "Fatal error: %s", error.what());
    return_code = 2;
  } catch (...) {
    RCLCPP_FATAL(rclcpp::get_logger("bt_executor"), "Unknown fatal error");
    return_code = 2;
  }

  if (rclcpp::ok()) {
    rclcpp::shutdown();
  }
  return return_code;
}
