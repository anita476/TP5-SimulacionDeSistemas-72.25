#pragma once
#include "include/fsm_pair.hpp"
#include "include/step.hpp"

/**
 * @brief Execute a step in a pair simulation.
 * @returns Step if successfull, NULL if something went wrong
 */
Step sfm_step(FSMPair particles, double time_step, double initial_time);