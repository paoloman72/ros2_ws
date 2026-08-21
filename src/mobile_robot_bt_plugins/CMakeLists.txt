cmake_minimum_required(VERSION 3.20)
project(mobile_robot_bt_plugins)

find_package(ament_cmake REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(rclcpp REQUIRED)

add_library(${PROJECT_NAME} SHARED
  src/custom_hello.cpp
  src/plugin_registration.cpp
)

target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

target_compile_definitions(${PROJECT_NAME} PRIVATE
  BT_PLUGIN_EXPORT
)

ament_target_dependencies(${PROJECT_NAME}
  behaviortree_cpp
  rclcpp
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