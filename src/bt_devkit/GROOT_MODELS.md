# Custom nodes in Groot2

Every mission built with `bt_devkit_add_mission()` exports its registered
custom nodes to `share/<mission>/groot/node_models.xml`. This includes the
devkit extra nodes registered by the plugin, even if the current tree does
not use them. Built-in BehaviorTree.CPP nodes are excluded.

## Build and import (ROS 2 Jazzy)

Inside the container:

```bash
source /opt/ros/jazzy/setup.bash
cd /ros2_ws
colcon build --packages-select bt_devkit my_mission wander_mission --symlink-install
source install/setup.bash
ls "$(ros2 pkg prefix my_mission)/share/my_mission/groot/node_models.xml"
ls "$(ros2 pkg prefix wander_mission)/share/wander_mission/groot/node_models.xml"
```

In Groot2, use **Import Models** and select the XML for the mission being
edited, then open its `behavior_trees/main.xml`. Import one mission's catalog
per project: the two plugins share several registration IDs.

If Groot2 runs on the Docker host, copy the generated files to the mounted
workspace from inside the container. This also dereferences symlinks whose
container paths may be inaccessible on the host:

```bash
mkdir -p /ros2_ws/groot_models
cp -L "$(ros2 pkg prefix my_mission)/share/my_mission/groot/node_models.xml" /ros2_ws/groot_models/my_mission.xml
cp -L "$(ros2 pkg prefix wander_mission)/share/wander_mission/groot/node_models.xml" /ros2_ws/groot_models/wander_mission.xml
```

With the usual `~/ros2_ws:/ros2_ws` mount, import
`~/ros2_ws/groot_models/my_mission.xml` or `wander_mission.xml` on the host.
Repeat the copy and import after changing node registrations or ports.
These are generated artifacts; do not maintain or commit them by hand.

## How generation works

The separate `bt_export_models` executable loads the freshly compiled
mission plugin into an empty factory and calls
`BT::writeTreeNodesModelXML(factory, false)`.
Registration IDs, node categories, ports, types, descriptions and defaults
come from the plugin's manifests and `providedPorts()`.
It does not construct a tree, tick nodes, or initialize ROS.
Registration callbacks must therefore remain usable without a ROS node.

The build target depends on the plugin and exporter: changing a port and
rebuilding regenerates the catalog. Deleting the generated build XML also
regenerates it on the next normal build. Export failures fail the build
instead of silently installing a stale catalog. One plugin per mission
package is the supported layout.

The executor, trees, runtime parameters and bundle registration contract
remain unchanged. No Gazebo session, running robot or Groot TCP port is
needed for export. The compiled plugin and its shared-library dependencies
must be available in the sourced Jazzy environment.

Port type metadata does not implement live JSON serialization of custom
blackboard values such as `geometry_msgs::msg::PoseStamped`.

## Manual export and cross-compilation

To export an installed plugin to an arbitrary output path:

```bash
ros2 run bt_devkit bt_export_models \
  "$(ros2 pkg prefix wander_mission)/lib/wander_mission/libwander_mission_nodes.so" \
  /tmp/wander_mission_models.xml
```

The command returns 0 on success, 1 on export/write failure and 2 for invalid
arguments. The output directory is created as needed; an existing output is
replaced only after successful serialization and writing.

Automatic export defaults to ON for native builds and OFF when CMake detects
cross-compilation. To disable it explicitly:

```bash
colcon build --packages-select my_mission wander_mission \
  --cmake-args -DBT_DEVKIT_EXPORT_GROOT_MODELS=OFF
```

Re-enable with `-DBT_DEVKIT_EXPORT_GROOT_MODELS=ON` (the option is cached).
When disabled, export manually on a machine/container that can run the
target binaries. Previously installed XML files are not removed by disabling
the option and may be stale.

## Groot XML and bundles

Keep the exported catalog separate from the mission tree. If Groot saves a
`TreeNodesModel` section inside a tree, `bt_make_bundle.py` ignores it when
checking node usage and deriving navigation monitoring. Both compact
`<NavigateToPose .../>` and explicit `<Action ID="NavigateToPose" .../>`
syntax are recognized. All local `BehaviorTree` definitions are checked;
external XML includes are not expanded by this lightweight checker.

The standalone catalog is not added to the simulator ZIP. An embedded
metadata section is preserved in the copied tree; final platform validation
remains authoritative.

## Verify the change

After the build, import both catalogs separately in Groot2:

- `my_mission`: ExampleNode, GreetNode, CreatePose, NavigateToPose,
  WaitForRobotReady.
- `wander_mission`: ExampleNode, BatteryCheck, PickRandomPose,
  SimulatedBattery, CreatePose, FindFreeSpace, NavigateToPose,
  WaitForRobotReady.

Check port directions and defaults (for example, GreetNode's `who=world`
and WaitForRobotReady's `timeout=15`). Edit `providedPorts()`, rebuild and
reimport to verify that the catalog follows the source.

For a runtime regression check without Gazebo:

```bash
ros2 launch bt_devkit mission.launch.py mission:=my_mission tree:=hello.xml use_sim_time:=false
```

With the usual simulation running, launch the same mission/namespace that
worked previously. Model export does not change how robots are addressed.

Packaging regression tests can run without ROS:

```bash
python3 -m unittest discover -s src/bt_devkit/test -v
```
