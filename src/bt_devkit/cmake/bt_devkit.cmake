# Helpers for mission projects built on top of bt_devkit.
#
# Usage in your CMakeLists.txt:
#
#   find_package(bt_devkit REQUIRED)
#   include(${bt_devkit_DIR}/bt_devkit.cmake)
#
#   bt_devkit_add_mission(my_mission_nodes
#     SOURCES src/my_node.cpp src/register_nodes.cpp
#     TREES   behavior_trees/main.xml behavior_trees/variants/other.xml
#     [DEPENDS rclcpp_action nav2_msgs ...]  # optional extra link deps
#   )
#
# This creates a single SHARED plugin library containing your custom nodes
# plus the devkit's extra nodes (the executor loads exactly one plugin .so
# per robot, so the extra-node sources are compiled INTO your plugin), and
# installs your trees under share/<your_package>/behavior_trees/
# (bundle-compatible layout: the source directory is already a bundle directory).
#
# This mirrors the CMake the simulator generates for uploaded bundles
# (bt_runtime_tools/scripts/bt_bundle_builder.py): ament_target_dependencies
# for rclcpp + behaviortree_cpp and the BT_PLUGIN_EXPORT compile definition
# for the registration symbol that bt_executor dlopen()s.

function(bt_devkit_add_mission target)
  cmake_parse_arguments(M "" "" "SOURCES;TREES;DEPENDS" ${ARGN})

  if(NOT M_SOURCES)
    message(FATAL_ERROR "bt_devkit_add_mission(${target}): SOURCES is required")
  endif()
  if(NOT bt_devkit_FOUND)
    message(FATAL_ERROR
      "bt_devkit_add_mission(${target}): call find_package(bt_devkit REQUIRED) first")
  endif()

  find_package(rclcpp REQUIRED)
  find_package(behaviortree_cpp REQUIRED)

  # ${bt_devkit_DIR} is <prefix>/share/bt_devkit/cmake -> <prefix> is three up.
  get_filename_component(_bt_devkit_prefix "${bt_devkit_DIR}/../../.." ABSOLUTE)

  # Devkit extra-node sources, installed by bt_devkit. GLOB is intentional:
  # adding a node to the devkit scaffold must not require editing missions.
  file(GLOB _devkit_extra_sources
    "${_bt_devkit_prefix}/share/bt_devkit/extra_nodes_src/*.cpp")
  if(NOT _devkit_extra_sources)
    message(FATAL_ERROR
      "bt_devkit_add_mission(${target}): no devkit extra-node sources found under "
      "${_bt_devkit_prefix}/share/bt_devkit/extra_nodes_src (rebuild/reinstall bt_devkit)")
  endif()

  add_library(${target} SHARED
    ${M_SOURCES}
    ${_devkit_extra_sources}
  )
  target_include_directories(${target} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${_bt_devkit_prefix}/include
  )
  # Platform plugin contract: export the registration entry point.
  target_compile_definitions(${target} PRIVATE BT_PLUGIN_EXPORT)
  # Extra DEPENDS (e.g. rclcpp_action, nav2_msgs) are linked the same way
  # the platform does from the manifest dependencies; keep them in sync with
  # your package.xml and bt_manifest.yaml.
  foreach(dep IN LISTS M_DEPENDS)
    find_package(${dep} REQUIRED)
  endforeach()
  ament_target_dependencies(${target}
    rclcpp
    behaviortree_cpp
    ${M_DEPENDS}
  )

  install(TARGETS ${target} DESTINATION lib/${PROJECT_NAME})

  foreach(tree IN LISTS M_TREES)
    install(FILES ${tree} DESTINATION share/${PROJECT_NAME}/behavior_trees)
  endforeach()
endfunction()
