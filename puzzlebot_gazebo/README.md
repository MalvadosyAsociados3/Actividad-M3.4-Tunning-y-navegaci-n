# puzzlebot_gazebo

Gazebo Classic simulation package for the Puzzlebot.

## Contents

```
puzzlebot_gazebo/
├── worlds/
│   └── maze_world.world   # SDF v1.7 indoor maze (Building Editor)
├── config/
│   └── gazebo_bridge.yaml # Documentation: topic mapping info
└── launch/
    └── puzzlebot_gazebo.launch.py
```

## Launch

Start Gazebo with the maze and spawn the Puzzlebot:

```bash
ros2 launch puzzlebot_gazebo puzzlebot_gazebo.launch.py
```

Optional arguments:

```bash
ros2 launch puzzlebot_gazebo puzzlebot_gazebo.launch.py \
    x_pos:=0.0 y_pos:=0.0 z_pos:=0.05 yaw:=0.0
```

## ROS 2 interface

No `ros2_control` manager is needed. The Gazebo Classic plugins defined
in `puzzlebot.urdf.xacro` handle all ROS 2 communication directly:

| Topic | Direction | Plugin |
|---|---|---|
| `/odom` | published | `libgazebo_ros_diff_drive.so` |
| `/tf` (odom→base_footprint) | published | `libgazebo_ros_diff_drive.so` |
| `/cmd_vel` | subscribed | `libgazebo_ros_diff_drive.so` |
| `/scan` | published | `libgazebo_ros_ray_sensor.so` |

`robot_state_publisher` (started by this launch) publishes the remaining
TF transforms (base_footprint→base_link→lidar_link, etc.) from the URDF.
