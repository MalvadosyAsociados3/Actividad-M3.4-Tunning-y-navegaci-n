"""
puzzlebot_gazebo.launch.py
Launches Gazebo Classic with the maze world, spawns the Puzzlebot and
starts robot_state_publisher.  The libgazebo_ros_diff_drive plugin
handles odometry + cmd_vel, so no separate ros2_control manager is needed.
"""

import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_desc   = get_package_share_directory('puzzlebot_description')
    pkg_gazebo = get_package_share_directory('puzzlebot_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    xacro_file  = os.path.join(pkg_desc,   'urdf',   'puzzlebot.urdf.xacro')
    world_file  = os.path.join(pkg_gazebo, 'worlds', 'maze_world.world')

    # Process Xacro → URDF string (needed by robot_state_publisher and spawn_entity)
    robot_description = xacro.process_file(xacro_file).toxml()

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pos        = LaunchConfiguration('x_pos',  default='0.0')
    y_pos        = LaunchConfiguration('y_pos',  default='-1.4')
    z_pos        = LaunchConfiguration('z_pos',  default='0.05')
    yaw          = LaunchConfiguration('yaw',    default='1.5708')

    return LaunchDescription([

        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Use /clock from Gazebo'),
        DeclareLaunchArgument('x_pos',  default_value='0.0',   description='Spawn X'),
        DeclareLaunchArgument('y_pos',  default_value='-1.4', description='Spawn Y'),
        DeclareLaunchArgument('z_pos',  default_value='0.05', description='Spawn Z'),
        DeclareLaunchArgument('yaw',    default_value='1.5708', description='Spawn yaw'),

        # ── Gazebo Classic ────────────────────────────────────────────────
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={
                'world':   world_file,
                'verbose': 'false',
                'pause':   'false',
            }.items()
        ),

        # ── robot_state_publisher ─────────────────────────────────────────
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': use_sim_time,
            }],
            output='screen'
        ),

        # ── Spawn Puzzlebot in Gazebo ────────────────────────────────────
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name='spawn_puzzlebot',
            arguments=[
                '-topic',  'robot_description',
                '-entity', 'puzzlebot',
                '-x', x_pos, '-y', y_pos, '-z', z_pos, '-Y', yaw,
            ],
            output='screen'
        ),
    ])
