# wander_mission

bt_devkit mission with wandering, battery checks and Nav2 navigation.
For execution and robot namespaces, see
[MISSION_LAUNCH.md](../bt_devkit/MISSION_LAUNCH.md).

## Mission behavior

The tree waits for scan and TF, selects a free corridor from LiDAR data and
navigates to the goal. It waits between successful goals and checks simulated
battery charge at each loop iteration. Low battery, a failed goal search or a
failed navigation ends the loop and selects the return goal at `(0, 0)` in map.
Use distinct return targets when running multiple robots.

Configuration in `behavior_trees/main.xml`:

| Node and port | Mission value | Meaning |
|---|---|---|
| FindFreeSpace `min_distance` | 1.5 | Minimum candidate distance in metres |
| FindFreeSpace `max_distance` | 3.0 | Maximum candidate distance in metres |
| FindFreeSpace `random_score_margin` | 0.25 | Maximum score loss relative to the best candidate |
| Sleep `msec` | 2000 | Real-time pause after a successful wandering goal |

FindFreeSpace scores validated corridors as `distance - 0.5 * abs(angle)`
(distance in metres, angle in radians). It retains the farthest valid distance
per direction and selects uniformly among candidates within the score margin.
A margin of 0 selects the best candidate deterministically; positive values
must be finite. The random generator is seeded per node instance. Candidates
may repeat, and a single eligible candidate produces no variation. Corridor
checks complement Nav2 planning; they do not replace it.

Sleep is non-blocking and interruptible. It uses real time rather than ROS
simulation time. Failed goals skip the pause; the final return has no added
pause. Battery checks occur on loop iterations, not continuously.

## Extra nodes for Groot2

The build automatically creates `groot/node_models.xml` in this mission
folder, alongside `behavior_trees/`. This is a regular file. For container builds, open it from the host through
the corresponding workspace mount. Use Groot2's **Import Models**
to load it before editing the tree. A copy is also installed under the package
prefix for ROS tooling.

| Registered node | Purpose |
|---|---|
| ExampleNode | Shared devkit scaffold |
| BatteryCheck | Check battery messages |
| PickRandomPose | Choose random coordinates |
| SimulatedBattery | Simulate battery depletion inside the tree |
| CreatePose | Build a target pose |
| FindFreeSpace | Choose a goal using scan data |
| NavigateToPose | Send a Nav2 navigation goal |
| WaitForRobotReady | Wait for scan and map-to-base TF |

Ports and defaults are exported from the compiled plugin's `providedPorts()`;
there is no second XML definition to maintain. Rebuild and reimport after
changing ports or registrations.

See [GROOT_MODELS.md](../bt_devkit/GROOT_MODELS.md) for environment setup,
manual export and verification.
