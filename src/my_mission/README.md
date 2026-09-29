# my_mission

Reference bt_devkit mission with greeting and navigation nodes.
For execution and robot namespaces, see
[MISSION_LAUNCH.md](../bt_devkit/MISSION_LAUNCH.md).

## Extra nodes for Groot2

The build automatically generates and installs
`share/my_mission/groot/node_models.xml` under the package prefix.
Use Groot2's **Import Models** to load this catalog before editing the tree.

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

See [GROOT_MODELS.md](../bt_devkit/GROOT_MODELS.md) for container commands,
host-accessible copies, manual export and verification.
