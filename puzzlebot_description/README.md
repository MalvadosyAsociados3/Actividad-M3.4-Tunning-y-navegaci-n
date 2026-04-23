# puzzlebot_description

Robot description package for the Puzzlebot differential-drive robot.

## Contents

```
puzzlebot_description/
├── urdf/
│   └── puzzlebot.urdf.xacro   # Full Xacro model with collision, inertial,
│                               # and Gazebo sensor/drive plugins
├── meshes/
│   ├── Puzzlebot_Jetson_Lidar_Edition_Base.stl
│   ├── Puzzlebot_Wheel.stl
│   └── Puzzlebot_Caster_Wheel.stl
├── rviz/
│   └── puzzlebot_description.rviz
└── launch/
    └── puzzlebot_description.launch.py
```

## Launch

Visualise the robot model and TF tree (no Gazebo required):

```bash
ros2 launch puzzlebot_description puzzlebot_description.launch.py
```

## URDF/Xacro structure

The Xacro file defines:

- **base_footprint** — ground-projection frame (origin at floor level)
- **base_link** — main chassis link (box 0.18 × 0.15 × 0.07 m)
- **wheel_r_link / wheel_l_link** — driven wheels (radius 0.05 m, separation 0.19 m)
- **caster_link** — passive front caster (sphere radius 0.02 m)
- **lidar_link** — LiDAR sensor frame (fixed at z = 0.08 m above base_link)

### Gazebo plugins embedded in the Xacro

| Plugin | Function |
|---|---|
| `libgazebo_ros_diff_drive.so` | Publishes `/odom` + `/tf` (odom→base_footprint); subscribes `/cmd_vel` |
| `libgazebo_ros_ray_sensor.so` | Publishes `/scan` (360° LaserScan from `lidar_link`) |
