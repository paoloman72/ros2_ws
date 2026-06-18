FROM ros:lyrical

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    ros-lyrical-turtlesim \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /ros2_ws

CMD source /opt/ros/lyrical/setup.bash && \
    colcon build --symlink-install && \
    source install/setup.bash && \
    exec bash