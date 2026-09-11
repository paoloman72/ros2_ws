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
| `scripts/bt_make_bundle.py` | Generates `bt_manifest.yaml` + the bundle ZIP from your project: nodes from `register_nodes.cpp`, deps from `package.xml`, tree from `behavior_trees/`; vendors Flow A nodes on request (`--vendor`). |

The reference mission is the workspace-level **`my_mission`** package
(one custom node + the vendored Nav2 navigation nodes, e2e-tested against
Gazebo + Nav2) — copy it to start a new mission.

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
produces is what Gate 1 (`bt_bundle_builder --validate-only`, guide §7.2)
validates.

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
  Gate 1 (`bt_bundle_builder --validate-only`) runs on that directory.
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
snippet is generated on the platform side (guide §6–9).

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
  This is the flow for navigation nodes copied from the reference bundle.

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
   `src/register_nodes.cpp` (Flow B) — the manifest entry is generated
   from this call at bundle time (Step 3).
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

3. Add `nav2_msgs` (and the other deps the nodes use) to your `package.xml`
   **and** to `DEPENDS` in `CMakeLists.txt` — the manifest's
   `dependencies` are generated from `package.xml`, so a green local build
   does not prove the dependencies are complete.

4. Their manifest entries (exact `id`/`class`/`header`) are generated from
   `register_nodes.cpp` at bundle time; `monitoring.actions` is added
   automatically when the tree uses `NavigateToPose`.

5. Run with your Gazebo world + Nav2 stack up (map, scan, TF, and the
   `navigate_to_pose` action) — same prereq as Gate 3 (guide §7.4).

This is exactly what the platform expects (bundles are self-contained);
`bt_make_bundle.py` stages the same files for you (Step 3).

## Roadmap: phase 2 — the converter

`bt_make_bundle.py` already automates the simple case: it scans the tree
for the node IDs actually used, resolves the registrations (including the
Flow A nodes from `bt_devkit::register_extra_nodes()`), vendors the Flow A
nodes, generates `bt_manifest.yaml` (dependencies, `monitoring.actions`),
shows the manifest for review, and — only when run without `--dry-run` —
produces the flat ZIP.

The platform-side converter remains the final authority; the remaining
phase-2 work is to align the two (e.g. also emit the robot
`config_json`/curl snippet locally, richer `monitoring` heuristics).

## Keeping the executor identical

    scripts/check_executor_sync.sh

If `bt_runtime_tools` is updated on the platform side, copy the new
`bt_executor.cpp` into this package and re-run the check.

## References

- `BT_MISSION_DEVELOPMENT_GUIDE.md` — the full development guide
- `BT_BUNDLE_PREPARATION_GUIDE.md` — bundle/packaging reference
- `custom_bt_example_success/` — 9 proven nodes + 4 trees (reference
  bundle, platform side)
- `src/my_mission/` — the local reference mission (e2e-tested; its bundle
  was generated by `bt_make_bundle.py`)
