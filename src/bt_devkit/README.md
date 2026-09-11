# bt_devkit

Local development kit for IPCEI custom Behavior Tree missions.

It lets you create, compile and test your own BT missions **locally, without
the online simulator**, using exactly the same executor the platform runs.

## What it contains

| Component | Notes |
|---|---|
| `bt_executor` | **Identical copy** of the simulator's executor (`bt_runtime_tools/src/bt_executor.cpp`). Same parameters, same exit codes, same blackboard `node` contract. Verify with `scripts/check_executor_sync.sh`. |
| `bt_extra_nodes` (static lib) | The *structure* for extra nodes: one stateful `ExampleNode` skeleton (ports + blackboard `node` + onStart/onRunning/onHalted) and `register_extra_nodes()`, where you add your reusable nodes. |
| `cmake/bt_devkit.cmake` | `bt_devkit_add_mission()` helper: builds your single plugin `.so` (your nodes + extra nodes) and installs your trees. |

The reference mission is the workspace-level **`my_mission`** package
(one custom node + the vendored Nav2 navigation nodes, bundle-ready
manifest, e2e-tested against Gazebo + Nav2) — copy it to start a new
mission.

> The ready-made navigation nodes (WaitForRobotReady, NavigateToPose, ...)
> are intentionally NOT in this package: they live in the reference bundle
> `custom_bt_example_success/`, which doubles as documentation.
> `my_mission` carries locally vendored copies.

## Requirements

- **ROS 2 Jazzy** with **BehaviorTree.CPP v4 (4.9.0)** — the exact same
  version the online simulator runs: `ros-jazzy-behaviortree-cpp`
  (installed by rosdep as the `behaviortree_cpp` dependency).
  It is already present in the `ros2-jazzy-gazebo` dev container
  (pulled in by the Nav2 stack); nothing extra to install.
- A ROS 2 workspace where you can `colcon build`.

## Workflow

1. **Step 1** — create the mission package.
2. **Step 2** — test it locally with the simulator's executor.
3. **Step 3** — create the bundle ZIP for the online simulator.

---

## Step 1 — Create a new mission package

Fastest start: copy the reference mission and rename it (package name in
`package.xml`, `project()` + plugin target in `CMakeLists.txt`, the C++
namespace in your node files, `plugin.name` + the class namespace in
`bt_manifest.yaml`):

    cp -r src/my_mission src/my_new_mission
    colcon build --packages-select bt_devkit my_new_mission

Layout — your project directory **is** a bundle directory (the same layout
the platform expects: manifest at root + `behavior_trees/` + `include/`
+ `src/`):

    my_new_mission/
    ├── bt_manifest.yaml          # source of truth for the platform
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

Keep `DEPENDS` in sync with `package.xml` **and** the manifest's
`dependencies` — the platform builds from the manifest, so a green local
build does not prove the manifest is complete.

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
registration from the `nodes:` entries in `bt_manifest.yaml`.

### bt_manifest.yaml

    version: 1

    tree:
      main: behavior_trees/main.xml

    plugin:
      name: my_new_mission_nodes

    dependencies:
      - rclcpp
      - behaviortree_cpp
      # + everything listed in DEPENDS

    nodes:
      - id: MyNode
        class: my_new_mission::MyNode
        header: my_node.hpp

    monitoring:
      actions:
        - navigate_to_pose    # only if the mission navigates

Declare every node your trees use, with exact `id`/`class`/`header`
(`header` relative to `include/`). Keep the manifest in sync with your
nodes and trees from day 1 — Gate 1 (`bt_bundle_builder --validate-only`,
guide §7.2) runs on this directory.

---

## Step 2 — Test locally

### Build

    colcon build --packages-select bt_devkit my_new_mission
    source install/setup.bash

### Run with the same executor the simulator uses

(no ready/start files → starts immediately)

    ros2 run bt_devkit bt_executor --ros-args \
      -p bt_xml:=$(ros2 pkg prefix my_new_mission)/share/my_new_mission/behavior_trees/main.xml \
      -p plugin_library:=$(ros2 pkg prefix my_new_mission)/lib/my_new_mission/libmy_new_mission_nodes.so \
      -p groot_enabled:=true -p groot_port:=1669

Watch the tree live in Groot2 at `http://127.0.0.1:1669`.
Exit codes (identical to the platform): `0` SUCCESS, `1` FAILURE,
`2` init error, `3` unexpected status.

### Trees that need the robot (Nav2)

1. Bring up the world + Nav2 — the `mobile_robot` package of this
   workspace (headless container → server-only Gazebo):

       ros2 launch mobile_robot full_simulation.launch.py \
         gz_args:="-s -r $(ros2 pkg prefix mobile_robot)/share/mobile_robot/worlds/slam_world.world.sdf"

2. Run the executor with `-p use_sim_time:=true` added — the world
   provides `/clock` and Nav2/AMCL tick on sim time.
3. Namespace: the local sim runs in the root namespace (`/scan`,
   `/navigate_to_pose`), so do NOT pass `-r __ns:=/pluto` locally. On the
   platform the executor is launched with the robot's namespace remaps
   (guide §7.4).

---

## Step 3 — Create the bundle for the simulator

The bundle must be **self-contained**: the platform compiles the plugin
from the bundle's `include/` + `src/` and generates node registration
from the `nodes:` entries in `bt_manifest.yaml`.

| Included | Excluded (local-only) |
|---|---|
| `bt_manifest.yaml` | `src/register_nodes.cpp` (registration comes from the manifest) |
| `behavior_trees/*.xml` — the trees the platform runs | `CMakeLists.txt`, `package.xml` |
| `include/*.hpp` — every header a used node needs | build artifacts, local-only test trees |
| `src/*.cpp` — every source of a used node | trees using devkit extra nodes (Flow A) unless vendored (below) |

### If a tree uses a Flow A node: vendor it first

Flow A extra nodes live in `bt_devkit/extra_nodes/`; the platform has no
`bt_devkit`. Copy the node's header + source into the bundle's
`include/` + `src/` (keeping the class name/namespace) and add its
manifest entry. (The phase-2 converter automates this; until then keep
such manifest entries commented out.)

### Zip it

Flat zip, manifest at the zip root (no wrapper folder):

    mkdir -p /tmp/bt_bundle/my_new_mission/{behavior_trees,include,src}
    cp bt_manifest.yaml /tmp/bt_bundle/my_new_mission/
    cp behavior_trees/main.xml /tmp/bt_bundle/my_new_mission/behavior_trees/
    cp include/*.hpp /tmp/bt_bundle/my_new_mission/include/
    cp src/*.cpp /tmp/bt_bundle/my_new_mission/src/
    ( cd /tmp/bt_bundle/my_new_mission && zip -r ~/my_new_mission_bundle.zip . )
    unzip -l ~/my_new_mission_bundle.zip   # sanity check

(this is exactly how `bundles/my_mission_bundle.zip` was produced).

### Upload

After upload the platform runs Gate 1 (`--validate-only`) on the bundle
and builds the plugin from the manifest; the robot `config_json`/curl
snippet is generated on the platform side (guide §6–9).

---

## Node registration: one node, one place

- **Flow A — devkit extra nodes.** The node lives in `bt_devkit/extra_nodes/`
  (the `ExampleNode` skeleton) and is registered by `register_extra_nodes()`,
  compiled into your plugin by the CMake helper; your project stays clean.
  *Platform caveat:* bundles are self-contained, so these nodes have to be
  vendored (header + source + manifest entry) before upload (Step 3) — the
  phase-2 converter does this.
- **Flow B — project nodes.** The node lives in your project
  (`include/` + `src/` + a `register_nodes.cpp` entry for the local build
  + a `bt_manifest.yaml` entry for the platform). Self-contained: works
  locally and on the platform with no extra step. This is the flow for
  navigation nodes copied from the reference bundle.

Never register the same node ID in both flows (duplicate → registration
error).

## Adding a node

1. Copy `extra_nodes/include/bt_devkit/extra_nodes/example_node.hpp` +
   `extra_nodes/src/example_node.cpp` and rename (into
   `bt_devkit/extra_nodes/` for Flow A, into your project's `include/` +
   `src/` for Flow B).
2. Fill in `providedPorts()` and the tick logic
   (rules: `BT_MISSION_DEVELOPMENT_GUIDE.md` §3).
3. Register it: `factory.registerNodeType<YourNode>("YourNode");` in
   `extra_nodes/src/register_extra_nodes.cpp` (Flow A) or your
   `src/register_nodes.cpp` (Flow B), plus the `bt_manifest.yaml` entry.
4. Rebuild (`bt_devkit` for Flow A — missions pick up the sources
   automatically via GLOB — or your package for Flow B), and re-test
   (Step 2).

## Bringing navigation nodes into your project (Flow B)

The devkit does not ship the proven navigation nodes on purpose; they live in
`custom_bt_example_success/`, and `my_mission` already carries local copies.

1. Copy the file pairs you need from `my_mission`:

       cp src/my_mission/include/{wait_for_robot_ready,create_pose,navigate_to_pose}.hpp include/
       cp src/my_mission/src/{wait_for_robot_ready,create_pose,navigate_to_pose}.cpp src/

2. Add the new `.cpp` files to `SOURCES` in your `CMakeLists.txt`, and
   register the nodes in `src/register_nodes.cpp` (class names/namespace
   exactly as in the reference bundle headers):

       factory.registerNodeType<mobile_robot_bt::WaitForRobotReady>("WaitForRobotReady");
       factory.registerNodeType<mobile_robot_bt::CreatePose>("CreatePose");
       factory.registerNodeType<mobile_robot_bt::NavigateToPose>("NavigateToPose");

3. Add `nav2_msgs` (and the other deps the nodes use) to your `package.xml`,
   to `DEPENDS` in `CMakeLists.txt` **and** to the manifest `dependencies`
   — the platform builds from the manifest, so a green local build does not
   prove the manifest is complete.

4. Add the nodes to `bt_manifest.yaml` with exact `id`/`class`/`header`
   (`header` relative to `include/`); declare `monitoring.actions` if the
   mission navigates.

5. Run with your Gazebo world + Nav2 stack up (map, scan, TF, and the
   `navigate_to_pose` action) — same prereq as Gate 3 (guide §7.4).

This is exactly what the platform expects (bundles are self-contained):
you are just doing it by hand before uploading.

## Roadmap: phase 2 — the converter

A hybrid converter will take a project like this and produce the platform
bundle:

- scan the `behavior_trees/*.xml` trees for the node IDs actually used;
- resolve node registrations, including nodes registered inside
  `bt_devkit::register_extra_nodes()` (not only the literal
  `registerNodeType<...>` calls in your project);
- vendor Flow A nodes (header + source from `bt_devkit/extra_nodes/`) into
  the bundle and emit their manifest entries;
- generate/update `bt_manifest.yaml` (dependencies, `monitoring.actions`),
  show a dry-run diff, and — only after your review — produce the ZIP and
  the platform `config_json`/curl snippet.

## Keeping the executor identical

    scripts/check_executor_sync.sh

If `bt_runtime_tools` is updated on the platform side, copy the new
`bt_executor.cpp` into this package and re-run the check.

## References

- `BT_MISSION_DEVELOPMENT_GUIDE.md` — the full development guide
- `BT_BUNDLE_PREPARATION_GUIDE.md` — bundle/packaging reference
- `custom_bt_example_success/` — 9 proven nodes + 4 trees (reference
  bundle, platform side)
- `src/my_mission/` — the local reference mission (bundle-ready, e2e-tested)
