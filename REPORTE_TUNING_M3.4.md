# Reporte de Tuning — Actividad M3.4

**Equipo:** Luis Adrián Uribe Cruz, Grant Nathaniel Keegan, Diego Gerardo Sánchez Moreno, Héctor Gúmaro Guzmán Reyes
**Actividad:** M3.4 — Tuning y navegación

---

## Objetivo

Ajustar los parámetros del stack Nav2 con base en **observaciones concretas** del comportamiento del Puzzlebot en el laberinto, de modo que cumpla el requisito funcional:

> El robot debe cargar el mapa, localizarse de forma estable, planear rutas funcionales, navegar de un punto A a un punto B, y regresar nuevamente al punto A.

Cada cambio documentado sigue la lógica **Síntoma → Causa → Parámetro ajustado**.

---

## Contexto del robot y entorno

| Característica | Valor |
|---|---|
| Puzzlebot escalado | 70% del original |
| Footprint | 12.6 × 10.5 cm |
| Radio circunscrito | ~8.2 cm |
| Velocidad lineal máxima | 0.12 m/s |
| Velocidad angular máxima | 0.8 rad/s |
| LiDAR | 360°, 0.08-5.0 m, 10 Hz |
| Mapa | 0.05 m/px, pasillos de ~30 cm |

---

## Bloque 1 — Costmaps

### 1.1 Inflation radius bloqueando pasillos
- **Síntoma:** En RViz el planner marcaba el pasillo casi todo como "costo alto" (morado/magenta) y se negaba a trazar ruta.
- **Causa:** `inflation_radius = 0.35 m` excedía la semi-anchura del pasillo (15 cm), dejando sin carril libre.
- **Parámetro ajustado:** `inflation_radius: 0.15` y `cost_scaling_factor: 5.0` (decaimiento más rápido del costo al alejarse del muro).

### 1.2 Robot radius desalineado con footprint real
- **Síntoma:** Planner trazaba rutas que chocaban con esquinas.
- **Causa:** `robot_radius = 0.12` era del robot original, pero tras escalar al 70% el radio circunscrito es ~0.08 m.
- **Parámetro ajustado:** `robot_radius: 0.08` en ambos costmaps (local y global).

### 1.3 Costmap local poco reactivo
- **Síntoma:** El controller tardaba en reaccionar a obstáculos cercanos.
- **Causa:** `update_frequency: 5.0` era insuficiente para la tasa del controller (20 Hz).
- **Parámetro ajustado:** Subir `update_frequency` a **10.0 Hz** y `publish_frequency` de 2.0 a **5.0 Hz**. Se mantuvo el tamaño 3×3 m del rolling window (suficiente dado el alcance del LiDAR de 5 m y velocidad de 0.12 m/s).

### 1.4 Coherencia de resolución
- Se mantuvo `resolution: 0.05 m/px` en ambos costmaps para coincidir con la resolución del mapa estático.

---

## Bloque 2 — AMCL

### 2.1 Convergencia lenta y "teletransportes"
- **Síntoma:** Tras fijar la pose inicial, la nube de partículas tardaba en converger; tras colisiones, el robot "saltaba" a zonas lejanas del mapa.
- **Causa:** Los coeficientes `alpha1..alpha4 = 0.2` modelan un robot real con ruido de odometría alto. En Gazebo el diff-drive es casi perfecto, así que AMCL esperaba un ruido que no existía y generaba incertidumbre excesiva.
- **Parámetro ajustado:** Reducir `alpha1..alpha5` de **0.2 → 0.1** (confiar más en la odometría simulada).

### 2.2 Particle filter pesado sin beneficio
- **Síntoma:** Uso de CPU alto en AMCL sin diferencia perceptible en precisión.
- **Causa:** `max_particles: 2000` y `min_particles: 500` son valores generosos para entornos grandes; el laberinto cabe en una ventana de ~4×4 m.
- **Parámetro ajustado:** `max_particles: 1500`, `min_particles: 300`.

### 2.3 Actualizaciones poco frecuentes para robot pequeño
- **Síntoma:** La pose de AMCL se desincronizaba mientras el robot avanzaba despacio.
- **Causa:** `update_min_d: 0.25 m` requería 25 cm de movimiento para reactualizar; con el robot escalado (vel 0.12 m/s) eso es ~2 s sin actualizar.
- **Parámetro ajustado:** `update_min_d: 0.15`, `update_min_a: 0.15`.

### 2.4 Sin recuperación ante divergencia
- **Síntoma:** Una vez divergente, AMCL nunca se recuperaba.
- **Causa:** `recovery_alpha_slow/fast = 0.0` desactivaba la generación de partículas aleatorias.
- **Parámetro ajustado:** `recovery_alpha_slow: 0.001`, `recovery_alpha_fast: 0.1`.

### 2.5 Rangos del láser fuera de lo real
- **Síntoma:** AMCL usaba lecturas inválidas fuera del rango del sensor.
- **Parámetro ajustado:** `laser_max_range: 5.0` (rango físico real), `laser_min_range: 0.08` (coincide con el `min_range` del LiDAR tras escalado).

---

## Bloque 3 — Local Planner (Regulated Pure Pursuit)

### 3.1 Giros abiertos que chocaban
- **Síntoma:** El controlador anterior (DWB) generaba arcos amplios que colisionaban en curvas de 90° del laberinto.
- **Causa:** DWB optimiza trayectorias tipo Ackermann; combina avance + giro simultáneos, poco apropiado para diff-drive en espacios estrechos.
- **Parámetro ajustado:** Migrar a **`RegulatedPurePursuitController`** con `use_rotate_to_heading: true`. El robot se detiene, gira en sitio hasta alinearse con el siguiente punto del path, y luego avanza recto.

### 3.2 Velocidades excesivas para robot escalado
- **Síntoma:** Al chocar con una pared, la inercia "catapultaba" al robot.
- **Parámetro ajustado:** `desired_linear_vel: 0.12 m/s` (antes 0.22), `rotate_to_heading_angular_vel: 0.6 rad/s`, `max_angular_accel: 1.5 rad/s²`.

### 3.3 Lookahead demasiado largo para el tamaño del robot
- **Síntoma:** El robot cortaba curvas (miraba un punto del path que ya estaba dos esquinas adelante).
- **Causa:** `lookahead_dist: 0.3 m` era mayor que el radio del robot (0.08 m) × 3.
- **Parámetro ajustado:** `lookahead_dist: 0.25`, `min_lookahead_dist: 0.2`, `max_lookahead_dist: 0.35`.

### 3.4 Regulación de velocidad en curvas y cerca de paredes
- Se activaron `use_regulated_linear_velocity_scaling: true` y `use_cost_regulated_linear_velocity_scaling: true` para que el robot **frene automáticamente** al entrar en curva cerrada o al acercarse a paredes (detectado vía costmap inflado).

### 3.5 Tolerancia de llegada a la meta
- **Síntoma:** El robot se detenía 25 cm antes del goal porque la tolerancia era igual a la distancia al obstáculo.
- **Parámetro ajustado:** `xy_goal_tolerance: 0.15` y `yaw_goal_tolerance: 0.20` (antes 0.25/0.25). Valores proporcionales al tamaño del robot escalado.

### 3.6 Progress checker
- **Síntoma:** Nav2 cancelaba el goal con "failed to make progress".
- **Causa:** `required_movement_radius: 0.5 m` era inalcanzable entre dos curvas consecutivas a 12 cm/s.
- **Parámetro ajustado:** `required_movement_radius: 0.2`.

---

## Bloque 4 — Coherencia con el robot y el entorno

| Parámetro | Valor | Justificación |
|---|---|---|
| `robot_radius` | 0.08 m | Radio circunscrito del Puzzlebot escalado al 70% (diagonal 16.4 cm → radio 8.2 cm) |
| `inflation_radius` | 0.15 m | ~2× robot_radius, suficiente margen sin bloquear pasillos de 30 cm |
| `resolution` | 0.05 m/px | Coincide con resolución del mapa estático |
| `desired_linear_vel` | 0.12 m/s | Máxima del diff-drive escalado, con margen de seguridad |
| `lookahead_dist` | 0.25 m | ~3× robot_radius, balance entre anticipación y agresividad |
| `xy_goal_tolerance` | 0.15 m | ~2× robot_radius, realista para el tamaño del robot |
| `update_min_d` (AMCL) | 0.15 m | Distancia razonable para resincronizar a 12 cm/s |

---

## Bloque 5 — Cumplimiento del requisito "ir a B y regresar a A"

Se creó el script `puzzlebot_navigation2/scripts/go_and_return.py` que:

1. Obtiene la pose actual del robot vía TF (`map → base_footprint`) → la guarda como **punto A**
2. Envía goal al **punto B** (parametrizable por CLI)
3. Espera N segundos en B
4. Reenvía goal al punto A guardado
5. Reporta éxito/fallo en cada etapa

**Uso:**

```bash
# Con B por defecto (1.0, 0.5, yaw 0.0); A se lee del TF actual
ros2 run puzzlebot_navigation2 go_and_return.py

# Con B personalizado
ros2 run puzzlebot_navigation2 go_and_return.py -- -x 1.2 -y 0.3 -Y 1.57

# Con ambos puntos fijos (útil para repetir la demostración)
ros2 run puzzlebot_navigation2 go_and_return.py -- \
    -x 1.2 -y 0.3 -Y 1.57 \
    --ax 0.0 --ay -1.4 --ayaw 1.5708
```

Usa `BasicNavigator` del paquete `nav2_simple_commander`, que implementa internamente la acción `NavigateToPose` y maneja feedback + cancelación.

---

## Resumen tabla de cambios aplicados

| Bloque | Parámetro | Antes | Después | Síntoma observado |
|---|---|---|---|---|
| Costmap | `inflation_radius` | 0.35 | **0.15** | Pasillos cubiertos de costo alto |
| Costmap | `cost_scaling_factor` | 3.0 | **5.0** | Decaimiento lento del costo |
| Costmap | `robot_radius` | 0.12 | **0.08** | Rutas chocando con esquinas |
| Costmap | `update_frequency` (local) | 5.0 | **10.0 Hz** | Reacción lenta a obstáculos |
| Costmap | `publish_frequency` (local) | 2.0 | **5.0 Hz** | RViz desincronizado |
| AMCL | `alpha1-5` | 0.2 | **0.1** | Particulas dispersas, convergencia lenta |
| AMCL | `max_particles` | 2000 | **1500** | CPU alta sin beneficio |
| AMCL | `min_particles` | 500 | **300** | idem |
| AMCL | `update_min_d` | 0.25 | **0.15 m** | Pose desincronizada con movimiento lento |
| AMCL | `update_min_a` | 0.20 | **0.15 rad** | idem |
| AMCL | `recovery_alpha_slow` | 0.0 | **0.001** | AMCL no se recuperaba tras divergir |
| AMCL | `recovery_alpha_fast` | 0.0 | **0.1** | idem |
| AMCL | `laser_max_range` | 100.0 | **5.0** | Rango fuera del real del sensor |
| AMCL | `laser_min_range` | -1.0 | **0.08** | idem |
| AMCL | `transform_tolerance` | 1.0 | **0.5** | Sincronía TF laxa |
| Controller | Plugin | DWB | **RPP** | Arcos amplios que chocaban en curvas cerradas |
| Controller | `desired_linear_vel` | 0.22 | **0.12 m/s** | Inercia excesiva al chocar |
| Controller | `lookahead_dist` | 0.3 | **0.25 m** | Robot cortaba curvas |
| Controller | `xy_goal_tolerance` | 0.25 | **0.15 m** | Robot se detenía lejos del goal |
| Controller | `yaw_goal_tolerance` | 0.25 | **0.20 rad** | idem |
| Controller | `required_movement_radius` | 0.5 | **0.2 m** | "Failed to make progress" entre curvas |
| Planner | `tolerance` | 0.5 | **0.25 m** | Ruta acababa en pasillo equivocado |
| Recoveries | `max_rotational_vel` | 1.0 | **0.8 rad/s** | Giros de recovery demasiado agresivos |
| Recoveries | `rotational_acc_lim` | 3.2 | **2.0 rad/s²** | idem |

---

## Conclusión

El proceso de tuning siguió tres principios:

1. **Proporcionalidad al robot:** casi todos los parámetros espaciales (`robot_radius`, `inflation_radius`, `lookahead_dist`, `xy_goal_tolerance`) se derivaron del radio circunscrito real del Puzzlebot escalado (~8 cm).
2. **Consistencia con la simulación:** se redujeron los coeficientes de ruido de AMCL (`alpha`) porque Gazebo entrega odometría casi perfecta, algo que no ocurre en hardware real.
3. **Selección del controlador adecuado:** la migración de DWB a Regulated Pure Pursuit fue el cambio de mayor impacto. Para diff-drive en espacios estrechos, la rotación en sitio (`use_rotate_to_heading: true`) permite cerrar curvas de 90° sin colisionar.

El script `go_and_return.py` cumple el requisito M3.4 de ir a B y regresar a A de forma autónoma, usando la API `BasicNavigator` para encapsular la lógica.
