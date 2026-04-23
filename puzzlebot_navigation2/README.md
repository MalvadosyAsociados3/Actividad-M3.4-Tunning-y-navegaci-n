# puzzlebot_navigation2

SLAM mapping and Nav2 autonomous navigation package for the Puzzlebot.

## Contents

```
puzzlebot_navigation2/
├── config/
│   ├── slam_toolbox.yaml  # SLAM Toolbox: online_async mapping mode
│   └── nav2_params.yaml   # Nav2 stack: AMCL, DWB, NavFn, costmaps, BT
├── maps/
│   ├── map_maze.pgm       # Pre-built occupancy grid map (0.05 m/px)
│   └── map_maze.yaml      # Map metadata (resolution, origin, thresholds)
├── rviz/
│   ├── slam.rviz          # Grid + Map + LaserScan + RobotModel + TF
│   └── nav2.rviz          # slam.rviz + AMCL particles + costmaps + paths
└── launch/
    ├── slam.launch.py     # Gazebo + SLAM Toolbox + RViz
    └── nav2.launch.py     # Gazebo + Nav2 bringup + RViz
```

## SLAM mapping

```bash
ros2 launch puzzlebot_navigation2 slam.launch.py
```

Drive manually in a separate terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Save the map when coverage is complete:

```bash
ros2 run nav2_map_server map_saver_cli \
    -f ~/puzzlebot_ws/src/puzzlebot_ros2/puzzlebot_navigation2/maps/map_maze
```

## Autonomous navigation

```bash
ros2 launch puzzlebot_navigation2 nav2.launch.py
```

Or supply a custom map:

```bash
ros2 launch puzzlebot_navigation2 nav2.launch.py \
    map:=/path/to/my_map.yaml
```

In RViz:
1. Use **2D Pose Estimate** to set the robot's initial position on the map.
2. Wait for the AMCL particle cloud to converge around the robot.
3. Use **Nav2 Goal** (2D Goal Pose) to send a navigation goal.

## Key parameters

| File | Notable settings |
|---|---|
| `slam_toolbox.yaml` | `resolution: 0.05`, `max_laser_range: 5.0`, loop closure ON |
| `nav2_params.yaml` | `max_vel_x: 0.22`, `max_vel_theta: 1.0`, `robot_radius: 0.12` |
