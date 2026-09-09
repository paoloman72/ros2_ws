cmake_minimum_required(VERSION 3.20)
project(bt_devkit)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(behaviortree_cpp REQUIRED)

# ---------------------------------------------------------------------------
# 1) bt_executor -- IDENTICAL to the simulator's executor
#    (gazebo/robot_ws/src/bt_runtime_tools/src/bt_executor.cpp).
#    Same parameters, same exit codes, same blackboard "node" contract.
#    Run scripts/check_executor_sync.sh to verify the copy has not drifted.
# ---------------------------------------------------------------------------
add_executable(bt_executor
  src/bt_executor.cpp
)
ament_target_dependencies(bt_executor
  rclcpp
  behaviortree_cpp
)

# ---------------------------------------------------------------------------
# 2) bt_extra_nodes -- static library with the devkit's "extra" nodes.
#    Today it is intentionally only a SCAFFOLD: one stateful ExampleNode
#    skeleton (the structure to start from) plus register_extra_nodes().
#    Missions do NOT link this library: bt_devkit_add_mission() compiles the
#    same sources (installed to share/bt_devkit/extra_nodes_src) into the
#    mission's single plugin .so, mirroring the platform's bundle build.
# ---------------------------------------------------------------------------
add_library(bt_extra_nodes STATIC
  extra_nodes/src/example_node.cpp
  extra_nodes/src/register_extra_nodes.cpp
)
target_include_directories(bt_extra_nodes PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/extra_nodes/include>
  $<INSTALL_INTERFACE:include>
)
# Link via ament_target_dependencies, exactly like bt_runtime_tools does for
# bt_executor: in ROS 2 Jazzy BehaviorTree.CPP is ament-wrapped and exports
# its include directories separately (behaviortree_cpp_INCLUDE_DIRS), so the
# raw ${behaviortree_cpp_LIBRARIES} path alone would not provide the headers.
ament_target_dependencies(bt_extra_nodes
  rclcpp
  behaviortree_cpp
)

install(TARGETS
  bt_executor
  bt_extra_nodes
  DESTINATION lib/${PROJECT_NAME}
)
install(DIRECTORY
  extra_nodes/include/
  DESTINATION include
)
# Extra-node sources are compiled into each mission plugin (the executor
# loads exactly one .so per robot); the mission helper cmake/bt_devkit.cmake
# picks them up from share/bt_devkit/extra_nodes_src after installation.
install(DIRECTORY
  extra_nodes/src/
  DESTINATION share/${PROJECT_NAME}/extra_nodes_src
)
install(FILES
  cmake/bt_devkit.cmake
  DESTINATION share/${PROJECT_NAME}/cmake
)
install(PROGRAMS
  scripts/check_executor_sync.sh
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
