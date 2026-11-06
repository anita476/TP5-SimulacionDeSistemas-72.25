#include "include/sfm.hpp"
#include "include/fsm_pair.hpp"
#include "include/particle.hpp"
#include <cmath>

namespace {
// obs! ley de newton f1 = -f2
ContactForceInstance contact_force(FSMPair pair) {
  double dx = pair.left.x - pair.right.x, dy = pair.left.y - pair.right.y;
  double rij = std::sqrt(dx * dx + dy * dy);
  double eij = rij - (pair.left.r + pair.right.r);

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
driving_force_particle(Particle particle, std::pair<double, double> target,
                       double tau) {
  double dx = (target.first - particle.x);
  double dy = (target.second - particle.y);
  double dist = std::sqrt(dx * dx + dy * dy);

  // direction of desired vel
  double e0x = (dist > 1e-12) ? dx / dist : 0.0;
  double e0y = (dist > 1e-12) ? dx / dist : 0.0;

  return {particle.m * (particle.v0 * e0x - particle.vx / tau),
          particle.m * (particle.v0 * e0y - particle.vy / tau)};
};

DrivingForceInstance driving_force(FSMPair pair,
                                   std::pair<double, double> target_p1,
                                   std::pair<double, double> target_p2) {

  return {driving_force_particle(pair.left, target_p1, pair.tau),
          driving_force_particle(pair.right, target_p2, pair.tau)};
}

} // namespace
