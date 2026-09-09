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
| `examples/hello_mission/` | Minimal classic user project (1 custom node, 2 trees) — copy it to start. |

> The ready-made navigation nodes (WaitForRobotReady, NavigateToPose, ...)
> are intentionally NOT in this package: they live in the reference bundle
> `custom_bt_example_success/`, which doubles as documentation.

## Requirements

- **ROS 2 Jazzy** with **BehaviorTree.CPP v4 (4.9.0)** — the exact same
  version the online simulator runs: `ros-jazzy-behaviortree-cpp`
  (installed by rosdep as the `behaviortree_cpp` dependency).
  It is already present in the `ros2-jazzy-gazebo` dev container
  (pulled in by the Nav2 stack); nothing extra to install.
- A ROS 2 workspace where you can `colcon build`.

## Quickstart

1. Copy the example to your workspace (as a sibling package):

   ```bash
   cp -r bt_devkit/examples/hello_mission /path/to/your_ws/src/
   ```

2. Edit: `behavior_trees/*.xml`, `src/greet_node.cpp`, or add your own nodes
   (copy `bt_devkit/extra_nodes/src/example_node.cpp` + header as a template).
   Keep `bt_manifest.yaml` in sync — Gate 1 (`--validate-only`, guide §7.2)
   runs on this directory from day 1.

3. Build (bt_devkit must be in the same workspace or already installed):

   ```bash
   colcon build --packages-select bt_devkit hello_mission
   source install/setup.bash
   ```

4. Run locally with the same executor the simulator uses
   (no ready/start files → starts immediately):

   ```bash
   ros2 run bt_devkit bt_executor --ros-args \
     -r __ns:=/pluto -r /tf:=tf -r /tf_static:=tf_static \
     -p bt_xml:=$(ros2 pkg prefix hello_mission)/share/hello_mission/behavior_trees/hello.xml \
     -p plugin_library:=$(ros2 pkg prefix hello_mission)/lib/hello_mission/libhello_mission_nodes.so \
     -p groot_enabled:=true -p groot_port:=1669
   ```

   Watch the tree live in Groot2 at `http://127.0.0.1:1669`.
   Exit codes: `0` SUCCESS, `1` FAILURE, `2` init error, `3` unexpected
   status — identical to the platform.

5. When you are ready for the online simulator, package your project as a
   bundle. Your `bt_manifest.yaml` is already in place; the phase-2 converter
   (§Roadmap) will scan trees/nodes, vendor the devkit nodes, and produce the
   ZIP + `config_json`/curl snippet. Manual path: guide sections 6–9.

## Adding a node

1. Copy `extra_nodes/include/bt_devkit/extra_nodes/example_node.hpp` +
   `extra_nodes/src/example_node.cpp` into your project and rename.
2. Fill in `providedPorts()` and the tick logic
   (rules: `BT_MISSION_DEVELOPMENT_GUIDE.md` §3).
3. Register it in your `src/register_nodes.cpp`:
   `factory.registerNodeType<YourNode>("YourNode");`
   (or in `register_extra_nodes.cpp` if it is a reusable "extra" node).

The executor loads exactly ONE plugin `.so` per robot; `bt_devkit_add_mission`
already merges your nodes and the devkit's extra nodes into that single
library. Which file registers a node (your project vs the devkit) follows the
Flow A/B rule below — one node, one registration.

## Node registration: one node, one place

The executor loads exactly one plugin `.so`, and BehaviorTree.CPP rejects
duplicate registrations — so **every node is registered exactly once**, in
one of two flows:

- **Flow A — devkit extra nodes.** The node lives in `bt_devkit/extra_nodes/`
  and is registered by `register_extra_nodes()`, compiled into your plugin
  through the static library; your project stays clean. *Platform caveat:*
  bundles must be self-contained, so for the online simulator these nodes
  have to be vendored (header + source) into the bundle — the phase-2
  converter (§Roadmap below) does this.
- **Flow B — project nodes.** The node lives in your project
  (`include/` + `src/` + `register_nodes.cpp` + `bt_manifest.yaml` entry).
  Self-contained: works locally and on the platform with no extra step.
  This is the flow for navigation nodes copied from the reference bundle.

Never register the same node ID in both flows (duplicate → registration
error at tree load).

## The manifest from day 1

Your project directory **is** a bundle directory: same layout the platform
expects (manifest at root, `behavior_trees/`, `include/`, `src/`). So:

- Keep `bt_manifest.yaml` in sync with your nodes and trees as you go.
- Run Gate 1 on your project on every commit (guide §7.2):

  ```bash
  ros2 run bt_runtime_tools bt_bundle_builder \
    --source-dir ./<your_mission_pkg> --work-dir /tmp/bt_validate \
    --result-json /tmp/bt_validate.json --validate-only
  ```

  Manifest/tree/header drift is then caught *before* conversion, not after.
- Flow A nodes (e.g. `ExampleNode`) are not in the manifest while they live
  in `bt_devkit`; the converter vendors them at conversion time. If Gate 1
  flags a tree using such a node, either vendor the node (Flow B) or comment
  the node out of the tree for the validation run.

## Bringing navigation nodes into your project (Flow B)

The devkit does not ship the proven navigation nodes on purpose; they live
in `custom_bt_example_success/`. To develop with them locally:

1. Copy the file pairs you need into your project:

   ```bash
   cp custom_bt_example_success/include/{wait_for_robot_ready,create_pose,navigate_to_pose}.hpp include/
   cp custom_bt_example_success/src/{wait_for_robot_ready,create_pose,navigate_to_pose}.cpp src/
   ```

2. Add the new `.cpp` files to `SOURCES` in your `CMakeLists.txt`, and
   register the nodes in `src/register_nodes.cpp` (class names/namespace
   exactly as in the reference bundle headers):

   ```cpp
   factory.registerNodeType<mobile_robot_bt::WaitForRobotReady>("WaitForRobotReady");
   factory.registerNodeType<mobile_robot_bt::CreatePose>("CreatePose");
   factory.registerNodeType<mobile_robot_bt::NavigateToPose>("NavigateToPose");
   ```

3. Add `nav2_msgs` to your `package.xml` **and** to the manifest
   `dependencies` — the platform builds from the manifest, so a green local
   build does not prove the manifest is complete.

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

```bash
scripts/check_executor_sync.sh
```

If `bt_runtime_tools` is updated on the platform side, copy the new
`bt_executor.cpp` into this package and re-run the check.

## References

- `BT_MISSION_DEVELOPMENT_GUIDE.md` — the full development guide
- `BT_BUNDLE_PREPARATION_GUIDE.md` — bundle/packaging reference
- `custom_bt_example_success/` — 9 proven nodes + 4 trees (reference)
