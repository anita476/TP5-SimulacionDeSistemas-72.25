#pragma once
#include "fsm_pair.hpp"
#include <vector>

/*
* @brief Computes new desired velocity direction when theres a conflict. Must
use `is_conflicting()` first to check.
* @returns <e0x,e0y>

*/
std::pair<double, double>
new_desired_direction(Particle particle, Particle obstacle,
                      std::pair<double, double> target, double d_lat);

// check if theres a conflict from one particle to the other
bool is_conflicting(Particle particle, Particle pot_obstacle,
                    std::pair<double, double> target, double d_lat);