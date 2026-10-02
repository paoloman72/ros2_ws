# Avvio breve di una missione

Il launch configura l'executor e risolve le risorse della missione installata.
Eseguire i comandi dalla radice del workspace, in un ambiente ROS 2 Jazzy
nativo o in container. Per Docker, aprire una shell nel proprio container e
raggiungere la directory del workspace montato; vedere
[Workspace environment](README.md#workspace-environment).

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select bt_devkit wander_mission --symlink-install
source install/setup.bash
ros2 launch bt_devkit mission.launch.py mission:=wander_mission
```

Per una simulazione nel namespace `robot1`, aggiungere `robot:=robot1`.

Nei terminali successivi basta caricare i setup, senza ripetere la build:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Se ROS_DOMAIN_ID è stato impostato soltanto in un'altra shell,
impostare lo stesso valore anche qui.

Omettere `robot` per il namespace root; non passare `robot:=` vuoto. Per le missioni di navigazione, Gazebo e Nav2 devono essere già attivi.
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
la missione wander con lo stesso goal di ritorno: entrambe le istanze tornano a (0,0).
Assegnare prima destinazioni di ritorno distinte ed evitare goal manuali concorrenti.

Ogni publisher Groot usa due porte TCP consecutive. Esempio di assegnazione
esplicita con `nav_groot_port` per Nav2 e `port` per le missioni:

| Processo | Porte |
|---|---|
| Nav2 robot1 | 1667–1668 |
| Executor robot1 | 1669–1670 |
| Nav2 robot2 | 1671–1672 |
| Executor robot2 | 1673–1674 |

Le porte sono una convenzione, non vengono assegnate dal namespace. Verificare
i listener nell'ambiente di rete in cui viene eseguito l'executor:

```bash
ss -ltnp
```

La porta successiva deve essere libera anch'essa. Per esempio è possibile usare
`port:=1701` se 1701 e 1702 sono libere, impostando 1701 anche nel client Groot.
Non si cerca una porta libera automaticamente: il client deve conoscere una
porta stabile. Un errore di bind differisce da un timeout di connessione dal client;
usare un indirizzo raggiungibile dalla macchina di Groot2. Loopback indica
l'ambiente di rete del client. Con container o VM possono servire pubblicazione
o inoltro di entrambe le porte.
Impostare host e porta nella finestra di connessione di Groot2, non in un browser.

I remapping /tf, /tf_static e /scan vengono applicati all'intero processo, inclusi
i listener interni ai plugin. I nomi relativi (navigate_to_pose, scan, battery_state)
seguono il namespace del robot. Ulteriori nomi assoluti nei plugin non vengono
rimappati automaticamente.

Sono disponibili anche `use_sim_time`, `tick_period_ms`, `ready_file`, `start_file`.
Usare ready_file distinti per robot/esecuzione e barriere start_file intenzionalmente
condivise o separate. Il launch non modifica gli XML, non orchestra una flotta e
non avvia il simulatore.
