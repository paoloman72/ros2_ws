# wander_mission

bt_devkit mission with wandering, battery checks and Nav2 navigation.
For execution and robot namespaces, see
[MISSION_LAUNCH.md](../bt_devkit/MISSION_LAUNCH.md).

## Pause between goals

After each successful wandering goal, the tree waits 2 seconds before
starting the next loop iteration. Change `msec="2000"` on the
`Sleep name="Pause between goals"` node in `behavior_trees/main.xml`
to adjust the duration (milliseconds; 0 disables the delay).

Sleep is a built-in BehaviorTree.CPP node: it remains RUNNING while its
timer expires and supports halting without blocking the executor thread.
It uses elapsed real time, not ROS simulation time. The battery is checked
at the next iteration, after the pause; this does not introduce continuous
battery monitoring. A failed goal skips the pause and proceeds to the
existing return branch. No pause is added after the final return goal.

Rebuild `wander_mission` to refresh the installed tree, and regenerate the
source bundle before uploading it online. Sleep does not require a custom
registration or an extra entry in the generated Groot2 catalog.

## Extra nodes for Groot2

The build automatically creates `groot/node_models.xml` in this mission
folder, alongside `behavior_trees/`. This is a regular file, readable from
the host even when the build runs inside Docker. Use Groot2's **Import Models**
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

See [GROOT_MODELS.md](../bt_devkit/GROOT_MODELS.md) for container commands,
manual export and verification.
