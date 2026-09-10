cmake_minimum_required(VERSION 3.20)
project(my_mission)

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

include(${bt_devkit_DIR}/bt_devkit.cmake)

bt_devkit_add_mission(my_mission_nodes
  SOURCES
    src/greet_node.cpp
    src/register_nodes.cpp
    # Vendored navigation nodes (Flow B, from the reference bundle).
    src/create_pose.cpp
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

ament_package()
