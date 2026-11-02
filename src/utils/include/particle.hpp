#pragma once

typedef enum { FIXED, COMPRESSIBLE } ParticleType;

struct Particle {
  ParticleType type;
  double x, y, r, vx, vy;
  double m = 0.0;
  double r_min = 0.0;
  double r_max = 0.0;
};