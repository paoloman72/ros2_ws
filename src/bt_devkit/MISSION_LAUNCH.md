# Avvio breve di una missione

Il launch configura il processo senza modificare `src/bt_executor.cpp`.
Dopo il checkout del branch che contiene questo launch, entrare nel container
già avviato da `run_gazebo.sh`. Da un secondo terminale **sull'host**:

```bash
docker exec -it ros2_gz bash
```

Poi **dentro il container**, dalla directory del workspace:

```bash
source /opt/ros/jazzy/setup.bash
cd /ros2_ws
colcon build --packages-select bt_devkit wander_mission --symlink-install
source install/setup.bash
ros2 launch bt_devkit mission.launch.py mission:=wander_mission robot:=robot1
```

Nei terminali successivi basta caricare i setup, senza ripetere la build:

```bash
source /opt/ros/jazzy/setup.bash
cd /ros2_ws
source install/setup.bash
```

Il container deve essere già attivo. Non avviare una seconda simulazione per
aprire il terminale. Se ROS_DOMAIN_ID è stato impostato soltanto in un'altra shell,
impostare lo stesso valore anche qui.

Omettere `robot` per il namespace root; non passare `robot:=` vuoto. Gazebo e Nav2 devono essere già attivi.
Il plugin predefinito è `<prefix>/lib/<mission>/lib<mission>_nodes.so`, come
installato da bt_devkit_add_mission. Per altri nomi usare `plugin:=/percorso/file.so`.
L'XML predefinito è `share/<mission>/behavior_trees/main.xml`; usare
`tree:=hello.xml` oppure un percorso assoluto per selezionarlo.

Groot è disabilitato per default: nessuna porta di monitoraggio viene aperta.
Per abilitarlo:

```bash
ros2 launch bt_devkit mission.launch.py mission:=wander_mission robot:=robot1 groot:=true port:=1669
ros2 launch bt_devkit mission.launch.py mission:=wander_mission robot:=robot2 groot:=true port:=1673
```

Questi sono esempi di indirizzamento, non un invito a eseguire simultaneamente
la missione wander invariata: entrambe le istanze ritornano ancora a (0,0).
Assegnare prima destinazioni di ritorno distinte ed evitare goal manuali concorrenti.

Ogni publisher Groot usa due porte TCP consecutive. Con lo script run_gazebo.sh:

| Processo | Porte |
|---|---|
| Nav2 robot1 | 1667–1668 |
| Executor robot1 | 1669–1670 |
| Nav2 robot2 | 1671–1672 |
| Executor robot2 | 1673–1674 |

Le porte sono una convenzione: verificare eventuali altri processi sull'host
che condivide la rete del container. Per elencare i listener, eseguire sull'host:

```bash
ss -ltnp
```

La porta successiva deve essere libera anch'essa. Per esempio è possibile usare
`port:=1701` se 1701 e 1702 sono libere, impostando 1701 anche nel client Groot.
Non si cerca una porta libera automaticamente: il client deve conoscere una
porta stabile. Un errore di bind differisce da un timeout di connessione dal client;
con una VM verificare anche l'indirizzo IP usato da Groot. Se Groot gira fuori
VirtualBox, 127.0.0.1 non indica la VM: usare un indirizzo raggiungibile della VM.
Impostare host e porta nella finestra di connessione di Groot2, non in un browser.

I remapping /tf, /tf_static e /scan vengono applicati all'intero processo, inclusi
i listener interni ai plugin. I nomi relativi (navigate_to_pose, scan, battery_state)
seguono il namespace del robot. Ulteriori nomi assoluti nei plugin non vengono
rimappati automaticamente.

Restano disponibili `use_sim_time`, `tick_period_ms`, `ready_file`, `start_file`.
Usare ready_file distinti per robot/esecuzione e barriere start_file intenzionalmente
condivise o separate. Il launch non modifica gli XML, non orchestra una flotta e
non avvia il simulatore. Le verifiche di build/runtime devono essere fatte su Jazzy.
