# bt_devkit

Local development kit for IPCEI custom Behavior Tree missions.

It lets you create, compile and test your own BT missions **locally, without
the online simulator**, using exactly the same executor the platform runs.

> **Quick start:** `QUICKSTART.md` — the compact 3-step flow
> (create → test locally → bundle). This README is the full reference.

## What it contains

| Component | Notes |
|---|---|
| `bt_executor` | **Identical copy** of the simulator's executor (`bt_runtime_tools/src/bt_executor.cpp`). Same parameters, same exit codes, same blackboard `node` contract. Verify with `scripts/check_executor_sync.sh`. |
| `launch/mission.launch.py` | Short local command: resolves mission resources, applies robot namespace/remaps and optionally enables Groot. See [MISSION_LAUNCH.md](MISSION_LAUNCH.md). |
| `bt_extra_nodes` (static lib) | The *structure* for extra nodes: one stateful `ExampleNode` skeleton (ports + blackboard `node` + onStart/onRunning/onHalted) and `register_extra_nodes()`, where you add your reusable nodes. |
| `cmake/bt_devkit.cmake` | `bt_devkit_add_mission()` helper: builds your single plugin `.so` (your nodes + extra nodes) and installs your trees. |
| `scripts/bt_make_bundle.py` | Generates `bt_manifest.yaml` + the bundle ZIP from your project: nodes from `register_nodes.cpp`, deps from `package.xml`, tree from `behavior_trees/`; vendors Flow A nodes on request (`--vendor`). |

The reference mission is [my_mission](../my_mission/README.md), which contains
a greeting node and navigation nodes. Copy it to start a mission.
Navigation nodes such as WaitForRobotReady and NavigateToPose are available
in `src/my_mission/`; reusable DevKit nodes live in `extra_nodes/`.

## Requirements

- ROS 2 Jazzy and the `behaviortree_cpp` dependency. The platform compatibility
  target is BehaviorTree.CPP 4.9.0; align installed versions with the target
  simulator before deployment.
- A ROS 2 workspace with colcon and the package dependencies installed.
- Gazebo and Nav2 for navigation missions; they are not needed for a
  non-navigation tree or for model export.

Commands below run from the workspace root (the directory containing `src/`),
in a shell with ROS sourced. `/opt/ros/jazzy/setup.bash` is the standard binary
installation path; adapt it if ROS is installed elsewhere. The environment can
be native or containerized. Container images, mounts and startup scripts are
managed by the user and are not supplied by this repository.

## Workflow

1. **Step 1** — create the mission package.
2. **Step 2** — test it locally with the simulator's executor.
3. **Step 3** — create the bundle ZIP for the online simulator.

---

## Step 1 — Create a new mission package

Fastest start: copy the reference mission and rename it (package name in
`package.xml`, `project()` + plugin target in `CMakeLists.txt`, the C++
namespace in your node files):

    cp -r src/my_mission src/my_new_mission
    colcon build --packages-select bt_devkit my_new_mission

Layout — your project contains everything the bundle needs (the same
layout the platform expects: `behavior_trees/` + `include/` + `src/`);
`bt_manifest.yaml` is **generated** into the bundle by
`bt_make_bundle.py` in Step 3:

    my_new_mission/
    ├── behavior_trees/main.xml   # tree the platform runs (tree.main)
    ├── include/<node>.hpp        # your node headers (flat)
    ├── src/<node>.cpp            # your node sources
    ├── src/register_nodes.cpp    # LOCAL ONLY — excluded from the bundle
    ├── CMakeLists.txt            # LOCAL ONLY — excluded from the bundle
    └── package.xml               # LOCAL ONLY — excluded from the bundle

### CMakeLists.txt

    find_package(bt_devkit REQUIRED)
    include(${bt_devkit_DIR}/bt_devkit.cmake)

    bt_devkit_add_mission(my_new_mission_nodes
      SOURCES
        src/my_node.cpp
        src/register_nodes.cpp
      TREES
        behavior_trees/main.xml
      DEPENDS            # optional: extra link deps beyond rclcpp + BT
        rclcpp_action
        nav2_msgs
    )

Keep `DEPENDS` in sync with `package.xml` — the manifest's
`dependencies` are generated from it (Step 3), so a green local build
does not prove the dependencies are complete.

### register_nodes.cpp (local build only)

    #include "behaviortree_cpp/bt_factory.h"
    #include "bt_devkit/extra_nodes/register_extra_nodes.hpp"
    #include "my_node.hpp"

    // Plugin entry point (createPlugin) that bt_executor dlopen()s.
    // Single file: the executor loads exactly one plugin per robot.
    BT_REGISTER_NODES(factory)
    {
      // Flow A: devkit extra nodes (registered once, via the devkit).
      bt_devkit::register_extra_nodes(factory);
      // Flow B: your project nodes.
      factory.registerNodeType<my_new_mission::MyNode>("MyNode");
    }

The online simulator does NOT use this file: it generates node
registration from the `nodes:` entries in the generated
`bt_manifest.yaml` — derived from exactly these `registerNodeType`
calls by `bt_make_bundle.py` (Step 3).

### bt_manifest.yaml (generated, not hand-maintained)

The manifest is **generated at bundle time** by `bt_make_bundle.py`
(Step 3) from the project's sources of truth: `nodes:` from
`register_nodes.cpp`, `dependencies` from `package.xml`, `plugin.name`
from the `bt_devkit_add_mission()` target, `tree.main` from
`behavior_trees/` (default `main.xml`), and `monitoring.actions` when the
tree navigates. Never edit it by hand — if something is wrong, fix the
source (nodes, deps, trees) and re-generate. The staged bundle it
produces is the input to the platform validation stage. The platform validator
is external to this repository.

---

## Step 2 — Test locally

### Workspace environment

From the workspace root, build the selected mission and source its install:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select bt_devkit my_new_mission --symlink-install
source install/setup.bash
```

Replace `my_new_mission` with your package name. Source ROS and
`install/setup.bash` in each terminal used for ROS commands. Use the same
`ROS_DOMAIN_ID` as the robot or simulation.

For Docker, enter your already running container first. The placeholder below
must be replaced with its actual name; then change to the workspace directory
as mounted inside that container:

```bash
docker exec -it <container_name> bash
```

Opening another shell does not require starting another simulation.

### Run a mission

`mission.launch.py` configures the existing executable; it does not modify
`bt_executor.cpp`, the plugin ABI or the simulator bundle.

Quick check without a robot, using an installed non-navigation tree:

```bash
ros2 launch bt_devkit mission.launch.py mission:=my_new_mission tree:=hello.xml use_sim_time:=false
```

With Gazebo and Nav2 already active in the root namespace:

```bash
ros2 launch bt_devkit mission.launch.py mission:=my_new_mission
```

For a simulation started with `namespace:=robot1`:

```bash
ros2 launch bt_devkit mission.launch.py mission:=my_new_mission robot:=robot1
```

Omit `robot` for root; do not pass an empty `robot:=` argument.
The launch applies namespace and process-wide TF/scan remaps, including internal
plugin listeners. Relative action names such as `navigate_to_pose` select the
robot automatically. Frame IDs remain `map`, `odom`, `base_link`.
Simulation time defaults to true.

The default tree is `share/<mission>/behavior_trees/main.xml`; the default
plugin is `lib/<mission>/lib<mission>_nodes.so` under the package prefix.
Use `tree:=other.xml` (or an absolute XML path) and
`plugin:=/absolute/path/library.so` for overrides. The plugin target must follow
the default naming convention or be supplied explicitly.

### Custom node models for Groot2

Mission builds automatically export their custom node models, including
registered devkit extra nodes, to `src/<mission>/groot/node_models.xml`
(a regular file beside `behavior_trees/`, also installed under the package prefix).
Import that file using Groot2's **Import Models**. Ports and defaults come
from the compiled plugin, without changing the executor or running Gazebo.
See [GROOT_MODELS.md](GROOT_MODELS.md) for build/import commands and checks,
and the node catalogs in [my_mission](../my_mission/README.md) and
[wander_mission](../wander_mission/README.md).

### Groot monitoring

Groot is off by default. Add `groot:=true port:=1669` to monitor robot1,
or `groot:=true port:=1673` for robot2, provided both ports of each pair are free.
Example port allocation, configured explicitly with `nav_groot_port` for
Nav2 and `port` for each mission launch:

| Process | TCP ports |
|---|---|
| Nav2 robot1 | 1667–1668 |
| BT executor robot1 | 1669–1670 |
| Nav2 robot2 | 1671–1672 |
| BT executor robot2 | 1673–1674 |

Set the first port of the selected executor pair in Groot2. Use an address
reachable from the machine running Groot2. Loopback (`127.0.0.1`) works only
when the executor shares that network namespace, or the ports are forwarded
there. Containers and VMs may require port publication or forwarding for both
ports. Check listeners with `ss -ltnp` in the executor's network environment.
A bind error and a client connection timeout are different failures.

### Simulation prerequisites

Start Gazebo/Nav2 once, or reuse a running simulation. With the `mobile_robot`
package built and sourced, a root-namespace GUI simulation starts with:

```bash
ros2 launch mobile_robot full_simulation.launch.py
```

For a named robot add `namespace:=robot1`, then match it with `robot:=robot1`
in the mission launch. In a server-only setup, use `use_rviz:=false` and the
`gz_args` override; GPU LiDAR still needs a working rendering backend.

Run only one mission controller per robot and avoid concurrent manual goals.
The wander mission returns to (0,0): assign distinct return targets
before running two copies concurrently.

See [MISSION_LAUNCH.md](MISSION_LAUNCH.md) for launch options, and [MULTIROBOT.md](../mobile_robot/MULTIROBOT.md) for simulation setup.

Direct invocation uses `ros2 run bt_devkit bt_executor --ros-args ...`.
The executable's exit codes are `0` SUCCESS, `1` FAILURE, `2` init/tick
error, `3` unexpected status (interruption: `130`). Do not assume that the
surrounding `ros2 launch` process returns the same exit code.

---

## Step 3 — Create the bundle for the simulator

The bundle must be **self-contained**: the platform compiles the plugin
from the bundle's `include/` + `src/` and generates node registration
from the `nodes:` entries in `bt_manifest.yaml`.

Run `bt_make_bundle.py` (in `bt_devkit/scripts/`; also installed to
`lib/bt_devkit/` by `colcon build`). It generates the manifest from your
project, stages exactly what the platform needs, and zips it flat
(`bt_manifest.yaml` at the zip root, no wrapper folder):

    python3 src/bt_devkit/scripts/bt_make_bundle.py src/my_new_mission \
      -o bundles/my_new_mission_bundle.zip

- `--dry-run` derives everything and prints the manifest for review,
  writing nothing.
- `-t behavior_trees/<other>.xml` if the platform tree is not `main.xml`.
- the staging dir defaults to the zip path without `.zip` — keep it:
  the platform validator can consume that directory (external tooling).
- sanity check the artifact:
  `python3 -m zipfile -l bundles/my_new_mission_bundle.zip`

Included (everything else is excluded automatically):

| Included | Excluded (local-only) |
|---|---|
| generated `bt_manifest.yaml` | `src/register_nodes.cpp` (registration comes from the manifest) |
| the tree the platform runs (default `behavior_trees/main.xml`) | `CMakeLists.txt`, `package.xml` |
| `include/*.hpp` — every header a used node needs | build artifacts, trees not staged (e.g. local-only test trees) |
| `src/*.cpp` — every source of a used node | trees using devkit extra nodes (Flow A) unless vendored (below) |

### If a tree uses a Flow A node: vendor it

Flow A extra nodes live in `bt_devkit/extra_nodes/`; the platform has no
`bt_devkit`. The script detects this and refuses to build the bundle —
re-run with `--vendor` and it copies the node's header + source from the
devkit into the bundle and adds the manifest entry:

    python3 src/bt_devkit/scripts/bt_make_bundle.py src/my_new_mission \
      --vendor -o bundles/my_new_mission_bundle.zip

### Upload

After upload the platform runs Gate 1 (`--validate-only`) on the bundle
and builds the plugin from the manifest; the robot `config_json`/curl
snippet is generated on the platform side. Those tools are not included here.

(This is how `bundles/my_mission_bundle.zip` is produced.)

---

## Node registration: one node, one place

- **Flow A — devkit extra nodes.** The node lives in `bt_devkit/extra_nodes/`
  (the `ExampleNode` skeleton) and is registered by `register_extra_nodes()`,
  compiled into your plugin by the CMake helper; your project stays clean.
  *Platform caveat:* bundles are self-contained, so these nodes have to be
  vendored (header + source + manifest entry) before upload (Step 3) —
  `bt_make_bundle.py --vendor` does this.
- **Flow B — project nodes.** The node lives in your project
  (`include/` + `src/` + a `register_nodes.cpp` entry for the local build;
  the platform entry is generated from the same call in Step 3).
  Self-contained: works locally and on the platform with no extra step.
  This is the flow for navigation nodes copied from the reference mission.

Never register the same node ID in both flows (duplicate → registration
error).

## Adding a node

1. Copy `extra_nodes/include/bt_devkit/extra_nodes/example_node.hpp` +
   `extra_nodes/src/example_node.cpp` and rename (into
   `bt_devkit/extra_nodes/` for Flow A, into your project's `include/` +
   `src/` for Flow B).
2. Define `providedPorts()` and the tick logic. Use a StatefulActionNode for
   work that remains RUNNING across ticks; see the ExampleNode scaffold.
3. Register it: `factory.registerNodeType<YourNode>("YourNode");` in
   `extra_nodes/src/register_extra_nodes.cpp` (Flow A) or your
   `src/register_nodes.cpp` (Flow B) — the manifest entry is generated
   from this call at bundle time (Step 3).
4. Rebuild (`bt_devkit` for Flow A — missions pick up the sources
   automatically via GLOB — or your package for Flow B), and re-test
   (Step 2).

## Bringing navigation nodes into your project (Flow B)

Navigation node sources are provided by the `my_mission` package.

1. From the workspace root, copy the file pairs into your mission (replace
   `my_new_mission` with the destination package):

       cp src/my_mission/include/{wait_for_robot_ready,create_pose,navigate_to_pose}.hpp src/my_new_mission/include/
       cp src/my_mission/src/{wait_for_robot_ready,create_pose,navigate_to_pose}.cpp src/my_new_mission/src/

2. Add the new `.cpp` files to `SOURCES` in your `CMakeLists.txt`, and
   register the nodes in `src/register_nodes.cpp` (class names/namespace
   matching the copied headers):

       factory.registerNodeType<mobile_robot_bt::WaitForRobotReady>("WaitForRobotReady");
       factory.registerNodeType<mobile_robot_bt::CreatePose>("CreatePose");
       factory.registerNodeType<mobile_robot_bt::NavigateToPose>("NavigateToPose");

3. Add `nav2_msgs` (and the other deps the nodes use) to your `package.xml`
   **and** to `DEPENDS` in `CMakeLists.txt` — the manifest's
   `dependencies` are generated from `package.xml`, so a green local build
   does not prove the dependencies are complete.

4. Their manifest entries (exact `id`/`class`/`header`) are generated from
   `register_nodes.cpp` at bundle time; `monitoring.actions` is added
   automatically when the tree uses `NavigateToPose`.

5. Run with your Gazebo world + Nav2 stack up (map, scan, TF, and the
   `navigate_to_pose` action).

This is exactly what the platform expects (bundles are self-contained);
`bt_make_bundle.py` stages the same files for you (Step 3).

## Bundle validation

Use `--dry-run` to inspect the generated manifest, then generate the source
ZIP. Local compilation does not replace validation and execution in the target
platform environment. Upload interfaces and platform validation tools are
provided by the simulator deployment.

## Keeping the executor identical

`check_executor_sync.sh` compares this executor with
`src/bt_runtime_tools/src/bt_executor.cpp` in the same workspace. The
`bt_runtime_tools` package belongs to the simulator and is not included in
this repository. The check requires that source to be available at that path:

```bash
bash src/bt_devkit/scripts/check_executor_sync.sh
```

Keep the executor synchronized with the target platform version; implement
local launch configuration and authoring tools separately.

## References

- [Quickstart](QUICKSTART.md)
- [Mission launch](MISSION_LAUNCH.md)
- [Groot2 models](GROOT_MODELS.md)
- [Reference mission](../my_mission/README.md)
- [Wandering mission](../wander_mission/README.md)
- [Robot simulation](../mobile_robot/MULTIROBOT.md)

Platform-specific development guides, bundle validators and upload interfaces
are maintained with the target simulator; they are not part of this repository.
