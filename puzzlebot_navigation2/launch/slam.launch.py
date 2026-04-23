"""
slam.launch.py
Starts SLAM Toolbox in online-async mapping mode together with Gazebo and RViz.

Launch order:
  1. Gazebo + Puzzlebot  (puzzlebot_gazebo package)
  2. slam_toolbox        async_slam_toolbox_node  (slam_toolbox.yaml)
  3. RViz2               (slam.rviz)

Usage:
  ros2 launch puzzlebot_navigation2 slam.launch.py
  ros2 launch puzzlebot_navigation2 slam.launch.py use_sim_time:=true
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_nav2   = get_package_share_directory('puzzlebot_navigation2')
    pkg_gazebo = get_package_share_directory('puzzlebot_gazebo')

    slam_config = os.path.join(pkg_nav2, 'config', 'slam_toolbox.yaml')
    rviz_config = os.path.join(pkg_nav2, 'rviz',   'slam.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    return LaunchDescription([

        # ── Arguments ──────────────────────────────────────────────────────
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use /clock from Gazebo'
        ),

        # ── 1. Gazebo + Puzzlebot ──────────────────────────────────────────
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo, 'launch', 'puzzlebot_gazebo.launch.py')
            ),
            launch_arguments={'use_sim_time': use_sim_time}.items()
        ),

        # ── 2. SLAM Toolbox (online async mapping) ─────────────────────────
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                slam_config,
                {'use_sim_time': use_sim_time}
            ],
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
