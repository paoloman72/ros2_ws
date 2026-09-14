// Stand-in for the robot's battery driver, for local testing: publishes
// a sensor_msgs/BatteryState on /battery_state whose charge level drops
// over time. On a real robot drop this node and let the actual driver
// publish on the same topic - the tree does not change.
//
// Parameters:
//   topic            (string, default "battery_state")
//   initial_percent  (double, default 100.0)
//   drain_per_sec    (double, default 0.5)
//   period_sec       (double, default 1.0)

#include <algorithm>
#include <chrono>
#include <memory>
#include <stdexcept>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/battery_state.hpp"

namespace wander_mission
{

class BatterySimulator : public rclcpp::Node
{
public:
  BatterySimulator()
  : Node("battery_simulator")
  {
    declare_parameter<std::string>("topic", "battery_state");
    declare_parameter<double>("initial_percent", 100.0);
    declare_parameter<double>("drain_per_sec", 0.5);
    declare_parameter<double>("period_sec", 1.0);

    percent_ = get_parameter("initial_percent").as_double();
    drain_ = get_parameter("drain_per_sec").as_double();
    period_sec_ = get_parameter("period_sec").as_double();

    if (drain_ < 0.0 || period_sec_ <= 0.0 || percent_ < 0.0 || percent_ > 100.0) {
      throw std::runtime_error("battery_simulator: invalid parameter values");
    }

    const auto topic = get_parameter("topic").as_string();
    publisher_ = create_publisher<sensor_msgs::msg::BatteryState>(
      topic, rclcpp::QoS(10));

    publishState();

    timer_ = create_wall_timer(
      std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::duration<double>(period_sec_)),
      [this]() {
        percent_ = std::max(0.0, percent_ - drain_ * period_sec_);
        publishState();
      });

    RCLCPP_INFO(
      get_logger(),
      "battery_simulator: publishing %s every %.1fs, starting at %.1f%%, "
      "draining %.2f%%/s",
      topic.c_str(), period_sec_, percent_, drain_);
  }

private:
  void publishState()
  {
    auto msg = sensor_msgs::msg::BatteryState();
    msg.header.stamp = now();
    msg.present = true;
    msg.percentage = percent_;
    msg.voltage = 3.0 + 4.0 * percent_ / 100.0;
    msg.temperature = 25.0;
    publisher_->publish(msg);
  }

  rclcpp::Publisher<sensor_msgs::msg::BatteryState>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  double percent_{100.0};
  double drain_{0.5};
  double period_sec_{1.0};
};

}  // namespace wander_mission

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<wander_mission::BatterySimulator>());
  rclcpp::shutdown();
  return 0;
}