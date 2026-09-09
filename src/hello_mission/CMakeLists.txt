cmake_minimum_required(VERSION 3.20)
project(hello_mission)

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

bt_devkit_add_mission(hello_mission_nodes
  SOURCES
    src/greet_node.cpp
    src/register_nodes.cpp
  TREES
    behavior_trees/hello.xml
    behavior_trees/main.xml
)

ament_package()
