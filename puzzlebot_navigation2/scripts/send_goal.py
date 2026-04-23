#!/usr/bin/env python3
"""
send_goal.py  --  Envia un goal de navegacion al Puzzlebot via Nav2.

Uso:
  ros2 run puzzlebot_navigation2 send_goal.py              # goal por defecto
  ros2 run puzzlebot_navigation2 send_goal.py -- -x 1.0 -y 2.0 -Y 1.57

Requiere que Nav2 este activo y que se haya fijado una pose inicial
(2D Pose Estimate en RViz o set_initial_pose.py).
"""

import argparse
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import math


def create_goal_pose(navigator: BasicNavigator, x: float, y: float, yaw: float) -> PoseStamped:
    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.header.stamp = navigator.get_clock().now().to_msg()
    goal.pose.position.x = x
    goal.pose.position.y = y
    goal.pose.orientation.z = math.sin(yaw / 2.0)
    goal.pose.orientation.w = math.cos(yaw / 2.0)
    return goal


def main():
    parser = argparse.ArgumentParser(description='Enviar goal de navegacion al Puzzlebot')
    parser.add_argument('-x', type=float, default=1.0, help='Posicion x del goal (m)')
    parser.add_argument('-y', type=float, default=0.0, help='Posicion y del goal (m)')
    parser.add_argument('-Y', '--yaw', type=float, default=0.0, help='Orientacion yaw del goal (rad)')
    args = parser.parse_args()

    rclpy.init()
    navigator = BasicNavigator()

    navigator.waitUntilNav2Active()

    goal_pose = create_goal_pose(navigator, args.x, args.y, args.yaw)
    navigator.get_logger().info(
        f'Enviando goal -> x={args.x:.2f}, y={args.y:.2f}, yaw={args.yaw:.2f} rad'
    )
    navigator.goToPose(goal_pose)

    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            eta = feedback.estimated_time_remaining.sec
            navigator.get_logger().info(f'ETA: {eta} s', throttle_duration_sec=2.0)

    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.get_logger().info('Goal alcanzado exitosamente')
    elif result == TaskResult.CANCELED:
        navigator.get_logger().warn('Goal cancelado')
    elif result == TaskResult.FAILED:
        navigator.get_logger().error('No se pudo alcanzar el goal')

    navigator.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
