#include "include/sfm.hpp"
#include "include/fsm_pair.hpp"
#include "include/particle.hpp"
#include "include/quadratic_heuristic.hpp"
#include <cmath>

namespace {
// obs! ley de newton f1 = -f2
ContactForceInstance contact_force(FSMPair pair) {
  double dx = pair.left.x - pair.right.x, dy = pair.left.y - pair.right.y;
  double rij = std::sqrt(dx * dx + dy * dy);
  double eij = rij - (pair.left.r + pair.right.r);

  if (eij >= 0)
    return {{0.0, 0.0},
            {0.0, 0.0}}; // if they arent touching -> no contact force

  double enx = dx / rij, eny = dy / rij; // normal
  double etx = -eny, ety = enx;          // tangential

  double vt = (pair.left.vx - pair.right.vx) * etx +
              (pair.left.vy - pair.right.vy) * ety;

  double Fn = -eij * pair.kn;
  double Ft = vt * eij * pair.kt;

  std::pair<double, double> on_particle1 = {Fn * enx + Ft * etx,
                                            Fn * eny + Ft * ety};

  return {on_particle1, {-on_particle1.first, -on_particle1.second}};
}

std::pair<double, double>
driving_force_particle(FSMPair pair, std::pair<double, double> target,
                       double tau, bool right) {
  Particle particle, obstacle;
  if (right) {
    particle = pair.right;
    obstacle = pair.left;
  } else {
    particle = pair.left;
    obstacle = pair.right;
  }

  double e0x, e0y;
  double dx = (target.first - particle.x);
  double dy = (target.second - particle.y);
  double dist = std::sqrt(dx * dx + dy * dy);

  // are they conflicting ?
  double dist_between_particles =
      std::hypot((particle.x - obstacle.x), (particle.y - obstacle.y));
  if ((dist_between_particles <= pair.action_distance &&
       is_conflicting(particle, obstacle, target, pair.r_min))) {
    const auto dir =
        new_desired_direction(particle, obstacle, target, pair.r_min);
    e0x = dir.first;
    e0y = dir.second;
  } else {

    // direction of desired vel -> normal fst
    e0x = (dist > 1e-12) ? dx / dist : 0.0;
    e0y = (dist > 1e-12) ? dy / dist : 0.0;
  }

  return {particle.m * (particle.v0 * e0x - particle.vx / tau),
          particle.m * (particle.v0 * e0y - particle.vy / tau)};
};

DrivingForceInstance driving_force(FSMPair pair,
                                   std::pair<double, double> target_p1,
                                   std::pair<double, double> target_p2) {

  return {driving_force_particle(pair, target_p1, pair.tau, false),
          driving_force_particle(pair, target_p2, pair.tau, true)};
}

} // namespace

Step sfm_step(FSMPair &pair, double dt, double initial_time,
              std::pair<double, double> target_left,
              std::pair<double, double> target_right) {
  auto [fc_l, fc_r] = contact_force(pair);
  auto [fd_l, fd_r] = driving_force(pair, target_left, target_right);

  double ax_l = (fd_l.first + fc_l.first) / pair.left.m;
  double ay_l = (fd_l.second + fc_l.second) / pair.left.m;
  double ax_r = (fd_r.first + fc_r.first) / pair.right.m;
  double ay_r = (fd_r.second + fc_r.second) / pair.right.m;

  // update speed, then update positions // @todo revisar esto, maybe se
  // puede usar algo de verlet ?
  pair.left.vx += ax_l * dt;
  pair.left.vy += ay_l * dt;
  pair.right.vx += ax_r * dt;
  pair.right.vy += ay_r * dt;

  pair.left.x += pair.left.vx * dt;
  pair.left.y += pair.left.vy * dt;
  pair.right.x += pair.right.vx * dt;
  pair.right.y += pair.right.vy * dt;

  return {initial_time + dt, pair.left.x, pair.left.y, pair.right.x,
          pair.right.y};
}