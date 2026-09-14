cmake_minimum_required(VERSION 3.20)
project(wander_mission)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(bt_devkit REQUIRED)
find_package(sensor_msgs REQUIRED)  # battery_simulator executable

include(${bt_devkit_DIR}/bt_devkit.cmake)

bt_devkit_add_mission(wander_mission_nodes
  SOURCES
    src/battery_check.cpp
    src/pick_random_pose.cpp
    src/register_nodes.cpp
    # Vendored navigation nodes (Flow B, from the reference bundle).
    src/create_pose.cpp
    src/find_free_space.cpp
    src/navigate_to_pose.cpp
    src/wait_for_robot_ready.cpp
  TREES
    behavior_trees/hello.xml
    behavior_trees/main.xml
  DEPENDS
    rclcpp_action
    nav2_msgs
    geometry_msgs
    sensor_msgs
    tf2_ros
    tf2_geometry_msgs
)

# Stand-in battery driver for local tests (publishes /battery_state);
# on a real robot the actual battery driver replaces it.
add_executable(battery_simulator src/battery_simulator.cpp)
ament_target_dependencies(battery_simulator rclcpp sensor_msgs)
install(TARGETS battery_simulator RUNTIME DESTINATION lib/${PROJECT_NAME})

ament_package()
