# my_mission

Reference bt_devkit mission with greeting and navigation nodes.
For execution and robot namespaces, see
[MISSION_LAUNCH.md](../bt_devkit/MISSION_LAUNCH.md).

## Extra nodes for Groot2

The build automatically creates `groot/node_models.xml` in this mission
folder, alongside `behavior_trees/`. This is a regular file. For container builds, open it from the host through
the corresponding workspace mount. Use Groot2's **Import Models**
to load it before editing the tree. A copy is also installed under the package
prefix for ROS tooling.

| Registered node | Purpose |
|---|---|
| ExampleNode | Shared devkit scaffold |
| GreetNode | Greeting action |
| CreatePose | Build a target pose |
| NavigateToPose | Send a Nav2 navigation goal |
| WaitForRobotReady | Wait for scan and map-to-base TF |

Ports and defaults are exported from the compiled plugin's `providedPorts()`;
there is no second XML definition to maintain. Rebuild and reimport after
changing ports or registrations.

See [GROOT_MODELS.md](../bt_devkit/GROOT_MODELS.md) for environment setup,
manual export and verification.
