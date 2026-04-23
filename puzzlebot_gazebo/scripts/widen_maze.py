#!/usr/bin/env python3
"""
widen_maze.py
Escala las posiciones (x, y) de los muros en un archivo .world de Gazebo
por un factor dado para ensanchar los pasillos, manteniendo el grosor de los muros.

Uso:
  python3 widen_maze.py <archivo_entrada.world> <archivo_salida.world> [factor]

  factor por defecto = 1.5  (pasillos 50% mas anchos)

Como funciona:
  - Encuentra los <pose>x y z r p y</pose> dentro de <model> (muros)
  - Multiplica solo los valores x e y por el factor
  - No escala tamanos ni rotaciones
"""

import re
import sys


def widen_poses(content: str, factor: float) -> str:
    # Regex para <pose>x y z roll pitch yaw</pose> con 6 numeros flotantes
    pose_re = re.compile(
        r'<pose>\s*([-\d.e]+)\s+([-\d.e]+)\s+([-\d.e]+)\s+([-\d.e]+)\s+([-\d.e]+)\s+([-\d.e]+)\s*</pose>'
    )

    # Separamos el preambulo (luz y ground plane) del cuerpo (muros)
    # Usamos una heuristica simple: el primer <model> es el Maze, desde ahi escalamos
    split_marker = "<model name='Maze'"
    if split_marker not in content:
        # fallback: escalar TODO despues de la primera declaracion de state
        split_marker = '<state'
    idx = content.find(split_marker)
    if idx == -1:
        print("ADVERTENCIA: no se encontro el modelo Maze; escalando todo el archivo.")
        idx = 0

    preamble = content[:idx]
    body = content[idx:]

    def replace(m: re.Match) -> str:
        x = float(m.group(1)) * factor
        y = float(m.group(2)) * factor
        z = float(m.group(3))
        r = float(m.group(4))
        p = float(m.group(5))
        yw = float(m.group(6))
        return f'<pose>{x:g} {y:g} {z:g} {r:g} {p:g} {yw:g}</pose>'

    body_scaled = pose_re.sub(replace, body)
    return preamble + body_scaled


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2]
    factor = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5

    with open(in_file, 'r') as f:
        content = f.read()

    scaled = widen_poses(content, factor)

    with open(out_file, 'w') as f:
        f.write(scaled)

    print(f"OK: {in_file} -> {out_file} (factor={factor})")
    print(f"Los pasillos son {(factor-1)*100:.0f}% mas anchos.")


if __name__ == '__main__':
    main()
