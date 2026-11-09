#include "include/quadratic_heuristic.hpp"

namespace {
// por las dudas
double lagrange_2nd_order(double x0, double x1, double x2, double y0, double y1,
                          double y2, double value) {
  return ((((value - x1) * (value - x2)) / ((x0 - x1) * (x0 - x2))) * y0 +
          (((value - x0) * (value - x2)) / ((x1 - x0) * (x1 - x2))) * y1) +
         ((((value - x0) * (value - x1)) / ((x2 - x0) * (x2 - x1))) * y2);
}
// se evalúa para pendiente !!
double lagrange_2nd_order_derivative(double x0, double x1, double x2, double y0,
                                     double y1, double y2, double value) {
  return y0 * (2.0 * value - x1 - x2) / ((x0 - x1) * (x0 - x2)) +
         y1 * (2.0 * value - x0 - x2) / ((x1 - x0) * (x1 - x2)) +
         y2 * (2.0 * value - x0 - x1) / ((x2 - x0) * (x2 - x1));
}
} // namespace

// new e0x and e0y when obstacle is detected in direct line
// obtenemos por interpolación de lagrange !!
std::pair<double, double>
new_desired_direction(Particle particle, Particle obstacle,
                      std::pair<double, double> target, double r_min) {
  double obstacle_y = obstacle.y + r_min; // actual tangent
  const double dx = target.first - particle.x;
  const double dy = target.second - particle.y;
  const double dist_to_target = std::hypot(dx, dy);

  const double ux = dx / dist_to_target,
               uy = dy / dist_to_target; // versor hacia el target
  const double rx = uy, ry = -ux;        // versor a la derecha del target

  const double obs_x = obstacle.x - particle.x; // posicion obstaculo centrado
  const double obs_y = obstacle.y - particle.y;
  const double dist_to_obs =
      obs_x * ux + obs_y * uy; // distacnai de la particula al obstaculo;
  const double obs_edge =
      obs_x * rx + obs_y * ry +
      (r_min +
       obstacle.r); // distancia del centro del obs al borde "imaginario"

  // la pendiente se calcula como si la linea recta particula -> target fuera el
  // eje x
  const double m =
      lagrange_2nd_order_derivative(0.0 /* particula "en" 0,0*/, dist_to_obs,
                                    dist_to_target, 0.0, obs_edge, 0.0, 0.0);
  const double n = std::hypot(1.0, m);
  return {/*e0x*/ (ux + m * rx) / n, /*e0y*/ (uy + m * ry) / n};
}

bool is_conflicting(Particle particle, Particle pot_obstacle,
                    std::pair<double, double> target, double r_min) {
  const double dx = target.first - particle.x;
  const double dy = target.second - particle.y;
  const double dist_to_target = std::hypot(dx, dy);
  const double
      ux = dx / dist_to_target,
      uy =
          dy / dist_to_target; // versor from particle to target (straight line)
  const double rx = uy, ry = -ux; // to the right "" (signed )

  const double obs_x = pot_obstacle.x - particle.x;
  const double obs_y = pot_obstacle.y - particle.y;
  const double along = obs_x * ux + obs_y * uy; // distance along the line
  const double lateral = obs_x * rx + obs_y * ry;

  const double R = r_min + pot_obstacle.r;

  /* particle isnt on the target, obstacle is in front of the target, and iits
   * inside the circle*/
  return along > 0.0 && along < dist_to_target && std::abs(lateral) < R;
}