# QUICKSTART — from zero to bundle in 3 steps

Condensed version of `README.md`: create the mission → test it locally with
the platform's executor → generate the bundle.
Requires a sourced ROS 2 Jazzy environment, native or containerized. Run
commands from the workspace root. Gazebo and Nav2 are needed for navigation.
See [Requirements](README.md#requirements) for environment setup.

## 1. Create

Copy the reference mission and rename it:

```bash
cp -r src/my_mission src/my_new_mission
```

Rename in 4 places: `package.xml` (name), `CMakeLists.txt` (`project()` +
the `bt_devkit_add_mission()` target), and the C++ namespace in your node
`include/`/`src/` files + `register_nodes.cpp`.

Layout (the platform expects exactly this; `CMakeLists.txt`, `package.xml`
and `src/register_nodes.cpp` are **local-only**, excluded from the bundle):

```
my_new_mission/
├── behavior_trees/main.xml   # tree the platform runs (tree.main)
├── include/<node>.hpp
├── src/<node>.cpp
├── src/register_nodes.cpp    # every node registration → manifest `nodes:`
├── CMakeLists.txt            # single plugin via bt_devkit_add_mission()
└── package.xml               # deps → manifest `dependencies`
```

Rules of thumb:

- **One plugin `.so` per robot** — register every node your tree uses in
  `src/register_nodes.cpp` (one `BT_REGISTER_NODES` block).
- Navigation nodes (WaitForRobotReady, NavigateToPose, ...): copy the
  `include/`+`src/` pairs from `src/my_mission/` (Flow B), add them to
  `SOURCES`, and add their deps to **both** `DEPENDS` and `package.xml`.
- A node that waits across ticks (a topic, an action) must be a
  `StatefulActionNode` — a `SyncActionNode` that returns `RUNNING`
  aborts the tree (exit code `2`).
- A `Sequence` stops at the first failure: if work must continue after a
  guarded loop (e.g. "wander until battery low, then go home"), wrap the
  loop in `ForceSuccess`.
- `bt_manifest.yaml` is **generated**, never hand-edited.

## 2. Test locally

From the workspace root:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select bt_devkit my_new_mission --symlink-install
source install/setup.bash
```

For Docker, first enter your container and locate its mounted workspace; see
[Workspace environment](README.md#workspace-environment).

For an existing mission use its package name, e.g. `wander_mission`, in both
the build and launch commands. In each new terminal, source both
ROS and the workspace again.

**Quick check without a robot:**

```bash
ros2 launch bt_devkit mission.launch.py mission:=my_new_mission tree:=hello.xml use_sim_time:=false
```

**Navigation mission:** Gazebo and Nav2 must already be running.
For a robot in the root namespace:

```bash
ros2 launch bt_devkit mission.launch.py mission:=my_new_mission
```

For a simulation started with `namespace:=robot1`:

```bash
ros2 launch bt_devkit mission.launch.py mission:=my_new_mission robot:=robot1
```

The launch handles resource paths, simulated time, namespace and TF/scan
remapping. Omit `robot` for root instead of passing `robot:=`.
`bt_executor.cpp` stays identical to the simulator.

**Groot:** disabled by default. Add `groot:=true port:=1669` for robot1 or
`groot:=true port:=1673` for robot2, if the selected port and the next one are
free. These are example assignments, not automatic namespace-based allocation.
Configure a reachable executor address and the selected port in Groot2.
For containers or VMs, check the network configuration for both ports.

Do not run two unchanged wander missions concurrently: both return to (0,0).
Avoid manual goals while a mission controls the robot.

Full options, port troubleshooting and custom plugin paths:
[MISSION_LAUNCH.md](MISSION_LAUNCH.md). Direct invocation with `ros2 run` is also available. The launch is a local convenience and is not added to mission bundles.

## 3. Bundle for the online simulator

```bash
python3 src/bt_devkit/scripts/bt_make_bundle.py src/my_new_mission \
  -o bundles/my_new_mission_bundle.zip
```

- `--dry-run` — derive and print the manifest, write nothing.
- `--vendor` — required when the tree uses Flow A nodes (extra nodes that
  live in `bt_devkit`); vendors their sources so the bundle is
  self-contained.
- `-t behavior_trees/<other>.xml` — if the platform tree isn't `main.xml`.
- The staging dir (`<zip>` without `.zip`) is kept: Gate 1
  (external platform tooling) validates it.

Upload the zip — the platform compiles the plugin from the bundle's
`include/`+`src/` and generates node registration from `bt_manifest.yaml`.

---

Details, the full node-development rules and the platform gates: `README.md`.
