#!/usr/bin/env python3
"""
go_and_return.py  --  Demuestra el requisito M3.4 "ir al punto B y regresar al A".

Flujo:
  1. Guarda la pose actual del robot como punto A.
  2. Navega al goal B (definido por CLI o defaults).
  3. Espera unos segundos en B.
  4. Regresa al punto A.

Uso:
  # B por defecto (1.0, 0.5, yaw 0.0), A se toma de la pose actual (map)
  ros2 run puzzlebot_navigation2 go_and_return.py

  # B personalizado
  ros2 run puzzlebot_navigation2 go_and_return.py -- -x 1.2 -y 0.3 -Y 1.57

  # B personalizado y A personalizado (no usa la pose actual del TF)
  ros2 run puzzlebot_navigation2 go_and_return.py -- \
      -x 1.2 -y 0.3 -Y 1.57 --ax 0.0 --ay -1.4 --ayaw 1.5708

Requiere que Nav2 este activo (nav2.launch.py corriendo) y que se haya
fijado la pose inicial via 2D Pose Estimate o set_initial_pose.py.
"""

import argparse
import math
import sys
import time

import rclpy
from rclpy.duration import Duration
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def make_pose(navigator: BasicNavigator, x: float, y: float, yaw: float) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def go_to(navigator: BasicNavigator, label: str, pose: PoseStamped) -> bool:
    navigator.get_logger().info(
        f'>> Navegando a {label}: x={pose.pose.position.x:.2f}, '
        f'y={pose.pose.position.y:.2f}'
    )
    navigator.goToPose(pose)

    while not navigator.isTaskComplete():
        fb = navigator.getFeedback()
        if fb:
            eta = Duration.from_msg(fb.estimated_time_remaining).nanoseconds / 1e9
            dist = fb.distance_remaining
            navigator.get_logger().info(
                f'   {label}: distancia={dist:.2f} m, ETA={eta:.1f} s',
                throttle_duration_sec=2.0,
            )

    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.get_logger().info(f'== {label} alcanzado')
        return True
    elif result == TaskResult.CANCELED:
        navigator.get_logger().warn(f'!! {label} cancelado')
    elif result == TaskResult.FAILED:
        navigator.get_logger().error(f'!! No se pudo alcanzar {label}')
    return False


def main():
    parser = argparse.ArgumentParser(description='Ir al punto B y regresar al A')
    parser.add_argument('-x', type=float, default=1.0, help='Goal B: x (m)')
    parser.add_argument('-y', type=float, default=0.5, help='Goal B: y (m)')
    parser.add_argument('-Y', '--yaw', type=float, default=0.0, help='Goal B: yaw (rad)')
    parser.add_argument('--ax', type=float, default=None, help='A: x (default = pose actual)')
    parser.add_argument('--ay', type=float, default=None, help='A: y (default = pose actual)')
    parser.add_argument('--ayaw', type=float, default=None, help='A: yaw (default = pose actual)')
    parser.add_argument('--ix', type=float, default=None, help='Initial pose x (publica antes de navegar)')
    parser.add_argument('--iy', type=float, default=None, help='Initial pose y')
    parser.add_argument('--iyaw', type=float, default=None, help='Initial pose yaw')
    parser.add_argument('--wait', type=float, default=3.0, help='Segundos de espera en B')
    args = parser.parse_args()

    rclpy.init()
    navigator = BasicNavigator()

    # Nav2 corre con tiempo simulado de Gazebo. Forzamos use_sim_time=True
    # en este nodo para que el TransformListener sincronice correctamente
    # los timestamps de /tf con los del simulador.
    from rclpy.parameter import Parameter
    navigator.set_parameters([
        Parameter('use_sim_time', Parameter.Type.BOOL, True),
    ])

    # Publicar initial pose si se especifica (evita depender de script externo)
    if args.ix is not None and args.iy is not None:
        initial_pose = PoseStamped()
        initial_pose.header.frame_id = 'map'
        initial_pose.header.stamp = navigator.get_clock().now().to_msg()
        initial_pose.pose.position.x = args.ix
        initial_pose.pose.position.y = args.iy or 0.0
        iyaw = args.iyaw or 0.0
        initial_pose.pose.orientation.z = math.sin(iyaw / 2.0)
        initial_pose.pose.orientation.w = math.cos(iyaw / 2.0)
        navigator.setInitialPose(initial_pose)
        navigator.get_logger().info(
            f'Initial pose enviada: x={args.ix:.2f}, y={args.iy:.2f}, yaw={iyaw:.2f}'
        )
        # Dar tiempo a AMCL para converger con la pose inicial
        time.sleep(5.0)

    navigator.waitUntilNav2Active()

    # Determinar punto A
    if args.ax is not None and args.ay is not None and args.ayaw is not None:
        a_pose = make_pose(navigator, args.ax, args.ay, args.ayaw)
        navigator.get_logger().info(
            f'Punto A (manual): x={args.ax:.2f}, y={args.ay:.2f}, yaw={args.ayaw:.2f}'
        )
    else:
        # Usar la pose actual del robot (TF map->base_footprint) como punto A.
        # IMPORTANTE: dejar tiempo al TransformListener para que reciba los
        # mensajes /tf antes de intentar el lookup.
        from tf2_ros import Buffer, TransformListener
        tf_buffer = Buffer()
        tf_listener = TransformListener(tf_buffer, navigator, spin_thread=True)

        navigator.get_logger().info('Esperando TF map->base_footprint...')
        timeout_sec = 15.0
        deadline = time.time() + timeout_sec
        transform = None

        while time.time() < deadline:
            # Spin un poco para dejar que el listener procese /tf
            rclpy.spin_once(navigator, timeout_sec=0.1)
            try:
                if tf_buffer.can_transform(
                    'map', 'base_footprint', rclpy.time.Time(),
                    timeout=rclpy.duration.Duration(seconds=0.5),
                ):
                    transform = tf_buffer.lookup_transform(
                        'map', 'base_footprint', rclpy.time.Time()
                    )
                    break
            except Exception:
                pass

        if transform is None:
            navigator.get_logger().error(
                'No se pudo obtener TF map->base_footprint tras 15 s. '
                'Verifica que fijaste la pose inicial (2D Pose Estimate) '
                'y que AMCL publica map->odom. '
                'Como alternativa, pasa --ax --ay --ayaw manualmente.'
            )
            # no apagamos Nav2 para mantener activos map_server/AMCL
            rclpy.shutdown()
            sys.exit(1)

        t = transform.transform.translation
        q = transform.transform.rotation
        yaw = 2.0 * math.atan2(q.z, q.w)
        a_pose = make_pose(navigator, t.x, t.y, yaw)
        navigator.get_logger().info(
            f'Punto A (TF actual): x={t.x:.2f}, y={t.y:.2f}, yaw={yaw:.2f}'
        )

    b_pose = make_pose(navigator, args.x, args.y, args.yaw)
    navigator.get_logger().info(
        f'Punto B:             x={args.x:.2f}, y={args.y:.2f}, yaw={args.yaw:.2f}'
    )

    # A -> B
    if not go_to(navigator, 'B', b_pose):
        # no apagamos Nav2 para mantener activos map_server/AMCL
        rclpy.shutdown()
        sys.exit(1)

    navigator.get_logger().info(f'Espera de {args.wait:.1f} s en B...')
    time.sleep(args.wait)

    # Limpiar costmaps antes del regreso: el local_costmap acumula inflacion
    # del recorrido A->B y puede bloquear la planificacion del camino inverso.
    navigator.get_logger().info('Limpiando costmaps antes del regreso...')
    try:
        navigator.clearLocalCostmap()
        navigator.clearGlobalCostmap()
    except Exception as e:
        navigator.get_logger().warn(f'clearCostmaps fallo: {e}, intentando clearAll...')
        try:
            navigator.clearAllCostmaps()
        except Exception:
            pass
    # Dar tiempo al costmap para regenerarse con datos frescos del LiDAR
    time.sleep(3.0)

    # B -> A
    # Re-timestamp antes de enviar
    a_pose.header.stamp = navigator.get_clock().now().to_msg()
    if not go_to(navigator, 'A (regreso)', a_pose):
        # no apagamos Nav2 para mantener activos map_server/AMCL
        rclpy.shutdown()
        sys.exit(1)

    navigator.get_logger().info('Ciclo A -> B -> A completado.')
    # no apagamos Nav2 para mantener activos map_server/AMCL
    rclpy.shutdown()


if __name__ == '__main__':
    main()
