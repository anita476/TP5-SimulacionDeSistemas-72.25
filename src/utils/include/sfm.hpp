#pragma once
#include "fsm_pair.hpp"
#include "step.hpp"
#include <vector>

struct ContactForceInstance {
  std::pair<double, double>
      force_particle_1; // ON particle 1 caused by particle 2
  std::pair<double, double> force_particle_2;
};
struct DrivingForceInstance {
  std::pair<double, double> force_particle_1;
  std::pair<double, double> force_particle_2;
};

/**
 * @brief Execute a step in a pair simulation.
 * @returns Step if successfull, NULL if something went wrong
 */
Step sfm_step(FSMPair &pair, double dt, double initial_time,
              std::pair<double, double> target_left,
              std::pair<double, double> target_right);