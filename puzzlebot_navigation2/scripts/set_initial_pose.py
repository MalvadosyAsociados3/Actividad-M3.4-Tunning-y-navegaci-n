#!/usr/bin/env python3
"""
set_initial_pose.py  --  Publica la pose inicial de AMCL sin necesidad de RViz.

Uso:
  ros2 run puzzlebot_navigation2 set_initial_pose.py                    # origen (0, 0, 0)
  ros2 run puzzlebot_navigation2 set_initial_pose.py -- -x 0.5 -y 0.3 -Y 1.57
"""

import argparse
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped


class InitialPosePublisher(Node):
    def __init__(self, x: float, y: float, yaw: float):
        super().__init__('set_initial_pose')
        self.publisher = self.create_publisher(
            PoseWithCovarianceStamped, 'initialpose', 10
        )
        self.x = x
        self.y = y
        self.yaw = yaw
        # Publica varias veces porque AMCL puede no estar listo en el primer tick
        self.timer = self.create_timer(0.5, self.publish_pose)
        self.count = 0

    def publish_pose(self):
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(self.yaw / 2.0)
        # Covarianza estandar para pose conocida con precision moderada
        msg.pose.covariance[0] = 0.25   # x
        msg.pose.covariance[7] = 0.25   # y
        msg.pose.covariance[35] = 0.068 # yaw
        self.publisher.publish(msg)
        self.count += 1
        self.get_logger().info(
            f'Pose inicial publicada -> x={self.x:.2f}, y={self.y:.2f}, yaw={self.yaw:.2f} rad'
        )
        if self.count >= 5:
            rclpy.shutdown()


def main():
    # Defaults match the spawn position in puzzlebot_gazebo.launch.py
    # (x=0.0, y=-1.4, yaw=1.5708 — entrada del laberinto apuntando al norte)
    parser = argparse.ArgumentParser(description='Publicar pose inicial de AMCL')
    parser.add_argument('-x', type=float, default=0.0,    help='Posicion x inicial (m)')
    parser.add_argument('-y', type=float, default=-1.4,   help='Posicion y inicial (m)')
    parser.add_argument('-Y', '--yaw', type=float, default=1.5708, help='Orientacion yaw (rad)')
    args = parser.parse_args()

    rclpy.init()
    node = InitialPosePublisher(args.x, args.y, args.yaw)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
