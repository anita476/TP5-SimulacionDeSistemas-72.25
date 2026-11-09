#pragma once

typedef enum { FIXED, COMPRESSIBLE } ParticleType;

struct Particle {
  int id;
  ParticleType type;
  double x, y, r, vx, vy, v0 /* desired -> escalar */;
  double m = 0.0;
  double r_min = 0.0;
  double r_max = 0.0;
};