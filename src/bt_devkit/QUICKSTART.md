# QUICKSTART — from zero to bundle in 3 steps

Condensed version of `README.md`: create the mission → test it locally with
the platform's executor → generate the bundle.
Assumes a ROS 2 Jazzy container (Gazebo + Nav2 only for the full e2e test).

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
- `bt_manifest.yaml` is **generated**, never hand-edited.

## 2. Test locally

```bash
colcon build --packages-select bt_devkit my_new_mission
source install/setup.bash
```

**Quick check (no robot):** run a tree that doesn't touch the robot
(`hello.xml` on a fresh copy works out of the box):

```bash
ros2 run bt_devkit bt_executor --ros-args \
  -p bt_xml:=$(ros2 pkg prefix my_new_mission)/share/my_new_mission/behavior_trees/hello.xml \
  -p plugin_library:=$(ros2 pkg prefix my_new_mission)/lib/my_new_mission/libmy_new_mission_nodes.so \
  -p groot_enabled:=true -p groot_port:=1669
```

**Full mission (needs Nav2):**

1. Start your robot sim: Gazebo world + robot description + Nav2
   (localization, controllers, planner, `navigate_to_pose` action) —
   the tree's `WaitForRobotReady` covers the rest. In this workspace
   that is (headless; drop `gz_args` for the Gazebo GUI):

   ```bash
   ros2 launch mobile_robot full_simulation.launch.py \
     gz_args:="-s -r $(ros2 pkg prefix mobile_robot)/share/mobile_robot/worlds/slam_world.world.sdf"
   ```

2. Executor on the real tree — note `-p use_sim_time:=true` (sim provides
   `/clock`) and **no** `-r __ns:=/pluto` (local sim runs in the root
   namespace):

   ```bash
   ros2 run bt_devkit bt_executor --ros-args \
     -p use_sim_time:=true \
     -p bt_xml:=$(ros2 pkg prefix my_new_mission)/share/my_new_mission/behavior_trees/main.xml \
     -p plugin_library:=$(ros2 pkg prefix my_new_mission)/lib/my_new_mission/libmy_new_mission_nodes.so \
     -p groot_enabled:=true -p groot_port:=1669
   ```

Watch the tree live in Groot2 at `http://127.0.0.1:1669`.
Exit codes (same as the platform): `0` SUCCESS, `1` FAILURE, `2` init
error, `3` unexpected status.

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
  (`bt_bundle_builder --validate-only`) validates it.

Upload the zip — the platform compiles the plugin from the bundle's
`include/`+`src/` and generates node registration from `bt_manifest.yaml`.

---

Details, the full node-development rules and the platform gates: `README.md`.
