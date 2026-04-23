"""
puzzlebot_description.launch.py
Loads the robot URDF/Xacro, starts robot_state_publisher and opens RViz.
Useful for verifying the robot model and TF tree in isolation.
"""

import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('puzzlebot_description')

    xacro_file = os.path.join(pkg, 'urdf', 'puzzlebot.urdf.xacro')
    rviz_file  = os.path.join(pkg, 'rviz', 'puzzlebot_description.rviz')

    # Process Xacro → URDF string
    robot_description = xacro.process_file(xacro_file).toxml()

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use /clock from Gazebo when true'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': use_sim_time,
            }]
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_file],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
    ])
