#include "utils/include/dump.h"
#include "utils/include/file_parser.h"
#include "utils/include/sfm.hpp"
#include <argparse/argparse.hpp>
#include <cmath>

const double MASS = 10;
const double TAU = 0.5;
const int PRECISION = 8;

int main(int argc, char *argv[]) {
  argparse::ArgumentParser program("Elusion-TP5", "0.1",
                                   argparse::default_arguments::help);
  program.add_argument("--r").default_value(0.25).scan<'g', double>().help(
      "Radius of particles");
  program.add_argument("--dt")
      .default_value(0.066581442)
      .scan<'g', double>()
      .help("Time step, should be taken from experimental data");
  program.add_argument("--kn").default_value(1.2e5).scan<'g', double>().help(
      "Compression: Normal k");
  program.add_argument("--kt").default_value(2.4e5).scan<'g', double>().help(
      "Friction: Tangential k");
  program.add_argument("--out-path", "--out_path", "--outpath")
      .default_value("data/sim/")
      .help("Path for output files");
  program.add_argument("--traj_path", "--traj-path", "--trajpath")
      .default_value("data/cruces/prueba6.txt")
      .help("Path to the trajectory file");
  program.add_argument("--time_path", "--time-path", "--timepath")
      .default_value("data/tiempos_totales.txt");
  program
      .add_argument("--initial_speeds_path", "--initial-speeds-path",
                    "--initialspeedspath")
      .default_value("data/velocidades_iniciales.txt");
  program.add_argument("--v_path", "--v-path", "--vpath")
      .default_value("data/pruebas_speeds.txt")
      .help("Path to the median velocity file");
  program.add_argument("--r_min", "--r-min", "--rmin")
      .default_value(0.30)
      .scan<'g', double>()
      .help("Minimum radius from the othr particle that particles are willing "
            "to go near (used for heuristic)");
  program
      .add_argument("--action_distance", "--action-distance",
                    "--actiondistance")
      .default_value(5.0)
      .scan<'g', double>()
      .help("Distance to obstacle since which particle begins to act for "
            "elusion");
  program.add_argument("--initial_velocity", "--initial-velocity")
      .default_value(std::string("zero"))
      .choices("zero", "experimental")
      .help("Initial velocity of both pedestrians: zero, or the experimental "
            "one from --initial_speeds_path");

  try {
    program.parse_args(argc, argv);
  } catch (const std::exception &err) {
    std::cerr << err.what() << '\n';
    std::cerr << program;
    return 1;
  }
  try {
    std::string traj_path = program.get("--traj_path");
    std::string time_path = program.get("--time_path");
    std::string v_path = program.get("--v_path");
    std::string out_path = program.get("--out_path");
    std::string initial_speeds_path = program.get("--initial_speeds_path");

    double dt = program.get<double>("--dt");

    std::cout << "Model SFM\n";

    // get the test num
    int num = parse_test_num(traj_path);
    std::cout << "Simulating run " << num << "\n";

    // get the standard vels and pos
    SpeedRow vdata = read_speed(v_path, num);
    std::cout << "Particle left: " << vdata.particle_left
              << " average v: " << vdata.particle_left_speed << "\n";
    std::cout << "Particle right: " << vdata.particle_right
              << " average v: " << vdata.particle_right_speed << "\n";

    double tf = parse_final_time(time_path, num);
    if (tf <= 0) {
      throw std::invalid_argument("Couldnt get final time from traj\n");
    }
    std::cout << "Final time: " << tf << "\n";

    InitialPositions positions = parse_initial_positions(
        traj_path, vdata.particle_left, vdata.particle_right);

    // Obs!! Can use, @todo ask later
    InitialSpeeds speeds = parse_initial_speeds(
        initial_speeds_path, vdata.particle_left, vdata.particle_right, num);

    // initial velocity: zero (experiment) or the experimental one at the first frame
    const bool use_exp_v = program.get("--initial_velocity") == "experimental";
    Particle left = {
        .id = vdata.particle_left,
        .m = MASS,
        .r = program.get<double>("--r"),
        .type = FIXED,
        .v0 = vdata.particle_left_speed,
        .vx = use_exp_v ? speeds.particle_left_x : 0.0,
        .vy = use_exp_v ? speeds.particle_left_y : 0.0,
        .x = positions.particle_left_x,
        .y = positions.particle_left_y,
    };
    Particle right = {
        .id = vdata.particle_right,
        .m = MASS,
        .r = program.get<double>("--r"),
        .type = FIXED,
        .v0 = vdata.particle_right_speed,
        .vx = use_exp_v ? speeds.particle_right_x : 0.0,
        .vy = use_exp_v ? speeds.particle_right_y : 0.0,
        .x = positions.particle_right_x,
        .y = positions.particle_right_y,
    };
    FSMPair pair = {.kn = program.get<double>("--kn"),
                    .kt = program.get<double>("--kt"),
                    .left = left,
                    .right = right,
                    .tau = TAU,
                    .r_min = program.get<double>("--r_min"),
                    .action_distance =
                        program.get<double>("--action_distance")};
    // dump header
    std::ofstream out(out_path);
    if (!out.is_open()) {
      throw std::runtime_error("Could not open output file: " + out_path);
    }
    out << std::setprecision(PRECISION);
    write_sfm_traj_header(out);

    // until they reach the desired tf, step and dump
    // for left, the target is right initial position
    std::pair<double, double> target_left = {pair.right.x, pair.right.y};

    // for right, the target is left initial position
    std::pair<double, double> target_right = {pair.left.x, pair.left.y};

    const int frames = static_cast<int>(std::lround(tf / dt)) + 1;
    write_sfm_traj_step(out, pair, 0.0);
    for (int k = 1; k < frames; ++k) {
      sfm_step(pair, dt, (k - 1) * dt, target_left, target_right);
      write_sfm_traj_step(out, pair, k * dt);
    }

  } catch (const std::exception &err) {
    std::cerr << "error: " << err.what() << '\n';
    return 1;
  }
  return 0;
}