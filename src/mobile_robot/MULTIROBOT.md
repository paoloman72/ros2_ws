# Robot singolo e preparazione multirobot (ROS 2 Jazzy)

Il comando esistente resta valido, con namespace vuoto, modello `mobile_robot`,
spawn `(0, 0, 0.3)` e yaw `0`. `bt_executor` e i plugin delle missioni non cambiano.
Questa modifica prepara l'isolamento: non introduce coordinamento di flotta.

## Prima verifica: comportamento precedente

Dopo il checkout del branch, nel container e dalla radice del workspace:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src/mobile_robot --ignore-src -r -y --rosdistro jazzy
colcon build --packages-select mobile_robot --symlink-install
source install/setup.bash
ros2 launch mobile_robot full_simulation.launch.py --show-args
ros2 launch mobile_robot full_simulation.launch.py
```

Fermare prima le precedenti istanze di Gazebo, Nav2 ed executor. Per un avvio
senza RViz usare `use_rviz:=false`; `gz_args` conserva il significato precedente.

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
provare la missione BT abituale con il comando precedente. Non avviare goal
manuali mentre la missione controlla il robot.

I controlli automatici della configurazione possono essere eseguiti senza Gazebo:

```bash
python3 -m unittest discover -s src/mobile_robot/test -p test_simulation_config.py -v
```

## Seconda verifica: un solo robot con namespace

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

Esempio di avvio della missione esistente (dopo la build di bt_devkit/wander_mission):

```bash
ros2 run bt_devkit bt_executor --ros-args \
  -r __ns:=/robot1 \
  -r /tf:=/robot1/tf -r /tf_static:=/robot1/tf_static \
  -r /scan:=/robot1/scan \
  -p use_sim_time:=true \
  -p bt_xml:="$(ros2 pkg prefix wander_mission)/share/wander_mission/behavior_trees/main.xml" \
  -p plugin_library:="$(ros2 pkg prefix wander_mission)/lib/wander_mission/libwander_mission_nodes.so"
```

I remapping TF sono globali al processo, così valgono anche per i listener
interni ai plugin. L'action relativa `navigate_to_pose` risolve automaticamente
il namespace. I plugin con altri nomi assoluti richiedono remapping espliciti.
Per nodi in altri container/macchine verificare anche la comunicazione DDS.

## Organizzazione dei launch

- `world.launch.py`: Gazebo e un solo bridge `/clock`.
- `spawn_robot.launch.py`: modello, robot_state_publisher, bridge robot e alias TF LiDAR.
- `gazebo.launch.py`: compatibilità con l'avvio mondo + robot, senza Nav2.
- `robot.launch.py`: spawn e bringup dopo la stessa attesa di 8 secondi usata prima.
- `full_simulation.launch.py`: mondo + robot completo.
- `bringup.launch.py`: localizzazione e navigazione per il namespace richiesto.
- `slam.launch.py`: SLAM nel namespace richiesto; usarlo al posto di AMCL.

Argomenti principali di `robot.launch.py`/`full_simulation.launch.py`:
`namespace`, `robot_name`, `x`, `y`, `z`, `yaw`, `map`, `use_rviz`,
`nav_groot_port`, `default_nav_to_pose_bt_xml`.
La posa `x`, `y`, `yaw` inizializza sia lo spawn sia AMCL: si assume che il frame
map della mappa salvata sia allineato al mondo Gazebo. In caso contrario impostare
la posa corretta con il tool Initial Pose prima della navigazione.

## In seguito: due robot nello stesso mondo

Avviare `world.launch.py` una sola volta; poi usare `robot.launch.py` per ciascun
robot con namespace e nome Gazebo univoci, pose libere e separate, porte Groot
non sovrapposte. Non lanciare due volte `full_simulation.launch.py`.
Ogni robot ha map server, AMCL e Nav2 indipendenti, con la stessa mappa salvata.

Esempio di suddivisione porte sullo stesso host: Nav2 robot1 `1667` (e `1668`),
executor robot1 `1669` (e `1670`), Nav2 robot2 `1671` (e `1672`), executor robot2
`1673` (e `1674`). Le porte si assegnano con `nav_groot_port` e con l'esistente
parametro `groot_port` dell'executor. Rendere univoci anche gli eventuali
`ready_file` per robot/esecuzione; usare barriere `start_file` intenzionalmente
condivise o separate e pulire file di esecuzioni precedenti.

La missione wander attuale ritorna a `(0,0)` in map: prima di usarla con due
robot va definita una destinazione di ritorno distinta. La navigazione locale
non risolve automaticamente precedenze o stalli tra robot. Il completamento
runtime della prova a due robot e questi adattamenti di missione sono successivi
alla regressione con un robot.

## Limiti della validazione di questa PR

Verificati trasformazione dei parametri root/namespaced, isolamento dei bridge,
configurazione RViz, sintassi e generazione Xacro. ROS 2/Gazebo non sono disponibili
nell'ambiente di modifica: build, caricamento effettivo dei parametri nei nodi,
TF, lifecycle e movimento vanno verificati nel container Jazzy con i passi sopra.
Il timeout fisso di avvio e i giunti mobili restano quelli della configurazione
precedente e non vengono presentati come problemi risolti da questa modifica.
