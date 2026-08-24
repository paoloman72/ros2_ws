cmake_minimum_required(VERSION 3.20)
project(mobile_robot_bt_plugins)

find_package(ament_cmake REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(mobile_robot_bt REQUIRED)

add_library(${PROJECT_NAME} SHARED
  src/custom_hello.cpp
  src/plugin_registration.cpp
  src/navigate_to_pose.cpp
  src/find_free_space.cpp
  src/wait_for_robot_ready.cpp
)

target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# Allow finding headers from the mobile_robot_bt package in-source during development
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/../mobile_robot_bt/include>
)

target_compile_definitions(${PROJECT_NAME} PRIVATE
  BT_PLUGIN_EXPORT
)

ament_target_dependencies(${PROJECT_NAME}
  behaviortree_cpp
  rclcpp
  rclcpp_action
  nav2_msgs
  geometry_msgs
  sensor_msgs
  tf2_ros
  tf2_geometry_msgs
  mobile_robot_bt
)

install(
  TARGETS ${PROJECT_NAME}
  LIBRARY DESTINATION lib
)

install(
  DIRECTORY include/
  DESTINATION include
)

ament_package()