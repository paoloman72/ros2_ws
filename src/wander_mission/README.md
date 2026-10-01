# wander_mission

bt_devkit mission with wandering, battery checks and Nav2 navigation.
For execution and robot namespaces, see
[MISSION_LAUNCH.md](../bt_devkit/MISSION_LAUNCH.md).

## Goal variation

The wandering tree sets `random_score_margin="0.25"` on FindFreeSpace.
The node still checks the same LiDAR corridors and retains the farthest
valid distance for each direction. It scores them as
`distance - 0.5 * abs(angle)` (distance in metres, angle in radians), then
chooses uniformly among directions no more than 0.25 score units below
the best. This adds modest variation without relaxing the existing
range, corridor width or obstacle clearance checks. It does not replace
Nav2 planning or guarantee collision avoidance.

Set the margin to `0` to restore the previous deterministic choice.
The node default is 0; only this mission enables variation explicitly.
The margin must be finite and non-negative. A larger margin admits less
preferred corridors; it is not a distance or an angular noise amplitude.
Only one eligible corridor means the result remains deterministic, and
successive random selections may repeat. The generator is seeded once per
node instance, so runs are not reproducible by default.

Rebuild `wander_mission` and reimport its generated Groot2 model to see
the new port. Regenerate the source bundle before online deployment.
The existing two-second pauses and return branch remain unchanged.

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
