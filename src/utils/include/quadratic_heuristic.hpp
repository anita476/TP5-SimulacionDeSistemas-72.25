#pragma once
#include "fsm_pair.hpp"
#include <vector>

std::pair<double, double> apply_heuristic(Particle particle, double time_step,
                                          std::pair<double, double> target);
