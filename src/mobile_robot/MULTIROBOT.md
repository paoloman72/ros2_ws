# Simulazione con uno o più robot su ROS 2 Jazzy

I launch supportano un robot nel namespace root oppure più robot con namespace
separati. Il clock è condiviso; localizzazione e navigazione sono per robot.
L'isolamento dei namespace non introduce coordinamento di flotta.

Eseguire i comandi dalla radice del workspace in un ambiente Jazzy nativo o
in container. Immagini Docker, mount e script di avvio sono esterni alla repo.

## Robot nel namespace root

Preparare e avviare il package:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src/mobile_robot --ignore-src -r -y --rosdistro jazzy
colcon build --packages-select mobile_robot --symlink-install
source install/setup.bash
ros2 launch mobile_robot full_simulation.launch.py --show-args
ros2 launch mobile_robot full_simulation.launch.py
```

Fermare prima le precedenti istanze di Gazebo, Nav2 ed executor. Per un avvio
senza RViz usare `use_rviz:=false`; `gz_args` configura gli argomenti di Gazebo.

In un secondo terminale, dopo aver caricato gli stessi setup:

```bash
ros2 lifecycle get /amcl
ros2 lifecycle get /bt_navigator
ros2 param get /map_server yaml_filename
ros2 param get /bt_navigator default_nav_to_pose_bt_xml
ros2 run tf2_ros tf2_echo map base_link
```

AMCL e navigatore devono risultare `active`; la trasformazione deve essere
disponibile. Verificare mappa e scansioni in RViz, assegnare un goal libero e
provare la missione BT abituale con il launch di bt_devkit. Non avviare goal
manuali mentre la missione controlla il robot.

I controlli automatici della configurazione possono essere eseguiti senza Gazebo:

```bash
python3 -m unittest discover -s src/mobile_robot/test -p test_simulation_config.py -v
```

## Robot con namespace

Fermare completamente la prova precedente, quindi:

```bash
ros2 launch mobile_robot full_simulation.launch.py namespace:=robot1
```

Il nome Gazebo viene derivato dal namespace (`robot1`); `robot_name:=pluto`
permette di cambiarlo esplicitamente. Verificare:

```bash
ros2 topic info /robot1/cmd_vel -v
ros2 topic info /robot1/scan -v
ros2 action info /robot1/navigate_to_pose
ros2 lifecycle get /robot1/amcl
ros2 lifecycle get /robot1/bt_navigator
ros2 param get /robot1/local_costmap/local_costmap obstacle_layer.scan.topic
ros2 run tf2_ros tf2_echo map base_link --ros-args \
  -r /tf:=/robot1/tf -r /tf_static:=/robot1/tf_static
```

La costmap deve leggere `/robot1/scan`. RViz viene configurato automaticamente
per i topic del robot. Il clock resta `/clock`. Non devono esserci publisher
Nav2/robot sui topic radice `/cmd_vel`, `/scan`, `/odom`, `/tf`, `/tf_static`.
I frame interni restano `map`, `odom`, `base_link`: non aggiungere il namespace
ai frame dei goal. Buffer TF diversi non devono unire flussi con frame omonimi.

Per avviare la missione, aprire un altro terminale nello stesso ambiente ROS e
raggiungere la radice del workspace. Per un container vedere
[Workspace environment](../bt_devkit/README.md#workspace-environment).

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select bt_devkit wander_mission --symlink-install
source install/setup.bash
ros2 launch bt_devkit mission.launch.py mission:=wander_mission robot:=robot1
```

La build serve dopo le modifiche; nei terminali successivi basta caricare i setup.
Omettere `robot` per la simulazione root. Per Groot aggiungere
`groot:=true port:=1669`; per il secondo executor scegliere una coppia libera,
ad esempio `port:=1673`. Groot è disabilitato per default.

Il launch configura namespace, percorsi e remapping TF/scan senza modificare
`bt_executor`. L'action relativa `navigate_to_pose` risolve automaticamente il
namespace. Ulteriori nomi assoluti nei plugin richiedono remapping espliciti.
La missione wander prevede il ritorno a (0,0): modificarlo prima dell'uso
simultaneo di più istanze. Per nodi in altri container/macchine verificare DDS.

Vedere [MISSION_LAUNCH.md](../bt_devkit/MISSION_LAUNCH.md) per opzioni e diagnostica
delle porte. Il comando diretto `ros2 run bt_devkit bt_executor` resta disponibile.

## Organizzazione dei launch

- `world.launch.py`: Gazebo e un solo bridge `/clock`.
- `spawn_robot.launch.py`: modello, robot_state_publisher, bridge robot e alias TF LiDAR.
- `gazebo.launch.py`: compatibilità con l'avvio mondo + robot, senza Nav2.
- `robot.launch.py`: spawn e bringup con un ritardo di avvio di 8 secondi.
- `full_simulation.launch.py`: mondo + robot completo.
- `bringup.launch.py`: localizzazione e navigazione per il namespace richiesto.
- `slam.launch.py`: SLAM nel namespace richiesto; usarlo al posto di AMCL.

Argomenti principali di `robot.launch.py`/`full_simulation.launch.py`:
`namespace`, `robot_name`, `x`, `y`, `z`, `yaw`, `map`, `use_rviz`,
`nav_groot_port`, `default_nav_to_pose_bt_xml`.
La posa `x`, `y`, `yaw` inizializza sia lo spawn sia AMCL: si assume che il frame
map della mappa salvata sia allineato al mondo Gazebo. In caso contrario impostare
la posa corretta con il tool Initial Pose prima della navigazione.

## Due robot nello stesso mondo

Avviare `world.launch.py` una sola volta; poi usare `robot.launch.py` per ciascun
robot con namespace e nome Gazebo univoci, pose libere e separate, porte Groot
non sovrapposte. Non lanciare due volte `full_simulation.launch.py`.
Ogni robot ha map server, AMCL e Nav2 indipendenti, con la stessa mappa salvata.

Esempio di suddivisione porte sullo stesso host: Nav2 robot1 `1667` (e `1668`),
executor robot1 `1669` (e `1670`), Nav2 robot2 `1671` (e `1672`), executor robot2
`1673` (e `1674`). Le porte si assegnano con `nav_groot_port` e con l'argomento `port` di `mission.launch.py` (che imposta `groot_port` nell'executor). Rendere univoci anche gli eventuali
`ready_file` per robot/esecuzione; usare barriere `start_file` intenzionalmente
condivise o separate e pulire file di esecuzioni precedenti.

La missione wander ritorna a `(0,0)` in map: prima di usarla con due
robot va definita una destinazione di ritorno distinta. La navigazione locale
non risolve automaticamente precedenze o stalli tra robot.

## Controlli operativi

Verificare TF, lifecycle, scansioni e navigazione per ogni namespace. Il bringup
usa un ritardo fisso di 8 secondi: attendere che i nodi siano attivi prima di
lanciare una missione. Per goal con frame omonimi, mantenere separati i buffer TF.
