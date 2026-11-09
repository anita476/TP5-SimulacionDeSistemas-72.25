#pragma once
#include "fsm_pair.hpp"
#include "particle.hpp"
#include <ostream>

inline void write_sfm_traj_header(std::ostream &out) {
  out << "particle_id time x y vx vy\n";
}

inline void write_particle_row(std::ostream &out, const Particle &p, double t) {
  out << p.id << ' ' << t << ' ' << p.x << ' ' << p.y << ' ' << p.vx << ' '
      << p.vy << '\n';
}

inline void write_sfm_traj_step(std::ostream &out, const FSMPair &pair,
                                double t) {
  write_particle_row(out, pair.left, t);
  write_particle_row(out, pair.right, t);
}