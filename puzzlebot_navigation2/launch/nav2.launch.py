"""
nav2.launch.py
Starts Nav2 autonomous navigation using a pre-built map.

Launch order:
  1. Gazebo + Puzzlebot  (puzzlebot_gazebo package)
  2. map_server          (map_maze.yaml)
  3. amcl                (nav2_params.yaml — localisation)
  4. nav2_bringup        (planner, controller, bt_navigator, recoveries …)
  5. RViz2               (nav2.rviz)

Usage:
  ros2 launch puzzlebot_navigation2 nav2.launch.py
  ros2 launch puzzlebot_navigation2 nav2.launch.py map:=/absolute/path/to/map.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_nav2        = get_package_share_directory('puzzlebot_navigation2')
    pkg_gazebo      = get_package_share_directory('puzzlebot_gazebo')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    nav2_params = os.path.join(pkg_nav2, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(pkg_nav2, 'rviz',  'nav2.rviz')
    default_map = os.path.join(pkg_nav2, 'maps',  'map_maze.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    map_yaml     = LaunchConfiguration('map',         default=default_map)
    autostart    = LaunchConfiguration('autostart',   default='true')

    return LaunchDescription([

        # ── Arguments ──────────────────────────────────────────────────────
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use /clock from Gazebo'
        ),
        DeclareLaunchArgument(
            'map',
            default_value=default_map,
            description='Full path to the OGM YAML file'
        ),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Auto-start Nav2 lifecycle nodes'
        ),

        # ── 1. Gazebo + Puzzlebot ──────────────────────────────────────────
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo, 'launch', 'puzzlebot_gazebo.launch.py')
            ),
            launch_arguments={'use_sim_time': use_sim_time}.items()
        ),

        # ── 2. Nav2 bringup (includes map_server, amcl, planner, controller,
        #        bt_navigator, lifecycle_manager …) ──────────────────────────
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map':          map_yaml,
                'params_file':  nav2_params,
                'autostart':    autostart,
            }.items()
        ),

        # ── 3. RViz2 ───────────────────────────────────────────────────────
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
    ])
