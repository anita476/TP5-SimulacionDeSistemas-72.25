#pragma once
#include "particle.hpp"

struct FSMPair {
  Particle left;
  Particle right;
  double kn;
  double kt;
  double tau;
  double r_min;
  double action_distance;
};