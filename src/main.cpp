#include "utils/include/dump.h"
#include "utils/include/file_parser.h"
#include "utils/include/sfm.hpp"
#include <argparse/argparse.hpp>

const double MASS = 10;
const double TAU = 0.5;
const int PRECISION = 8;

int main(int argc, char *argv[]) {
  argparse::ArgumentParser program("Elusion-TP5", "0.1",
                                   argparse::default_arguments::help);
  program.add_argument("--type")
      .choices("sfm", "cpm")
      .default_value("sfm")
      .help("Type of model: SFM or CPM");
  program.add_argument("--r").default_value(0.25).scan<'g', double>().help(
      "Radius of particles (used only for SFM)");
  program.add_argument("--r_min", "--r-min", "--rmin")
      .default_value(0.10)
      .scan<'g', double>()
      .help("Solid radius, used for CPM (use with rmax)");
  program.add_argument("--r_max", "--r-max", "--rmax")
      .default_value(0.25)
      .scan<'g', double>()
      .help("Compressible radius, used for CPM (use with rmin)");
  program.add_argument("--dt")
      .default_value(0.066581442)
      .scan<'g', double>()
      .help("Time step, should be taken from experimental data");
  program.add_argument("--tf")
      .default_value(13.743811430)
      .scan<'g', double>()
      .help("Final time, should be taken from experimental data. Default is "
            "average from experimental data");
  program.add_argument("--kn").default_value(1.2e5).scan<'g', double>().help(
      "Compression: Normal k");
  program.add_argument("--kt").default_value(2.4e5).scan<'g', double>().help(
      "Friction: Tangential k");
  program.add_argument("--out-path", "--out_path", "--outpath")
      .default_value("data/sim/")
      .help("Path for output files");
  program.add_argument("--traj_path", "--traj-path", "--trajpath")
      .default_value("data/druces/pueba6.txt")
      .help("Path to the trajectory file");
  program.add_argument("--v_path", "--v-path", "--vpath")
      .default_value("data/pruebas_speeds.txt")
      .help("Path to the median velocity file");
  try {
    program.parse_args(argc, argv);
  } catch (const std::exception &err) {
    std::cerr << err.what() << '\n';
    std::cerr << program;
    return 1;
  }
  try {
    if (program.get("--type") == "sfm") {
      std::string traj_path = program.get("--traj_path");
      std::string v_path = program.get("--v_path");
      std::string out_path = program.get("--out_path");
      double tf = program.get<double>("--tf");
      double dt = program.get<double>("--dt");

      std::cout << "Model SFM\n";

      // get the test num
      int num = parse_test_num(traj_path);
      // get the standard vels and pos
      SpeedRow vdata = read_speed(v_path, num);
      InitialPositions positions = parse_initial_positions(
          traj_path, vdata.particle_left, vdata.particle_right);

      // create the two particles with the initial speed 0
      Particle left = {
          .id = vdata.particle_left,
          .m = MASS,
          .r = program.get<double>("--r"),
          .type = FIXED,
          .v0 = vdata.particle_left_speed,
          .vx = 0,
          .vy = 0,
          .x = positions.particle_left_x,
          .y = positions.particle_left_y,
      };
      Particle right = {
          .id = vdata.particle_right,
          .m = MASS,
          .r = program.get<double>("--r"),
          .type = FIXED,
          .v0 = vdata.particle_right_speed,
          .vx = 0,
          .vy = 0,
          .x = positions.particle_right_x,
          .y = positions.particle_right_y,
      };
      FSMPair pair = {
          .kn = program.get<double>("--kn"),
          .kt = program.get<double>("--kt"),
          .left = left,
          .right = right,
          .tau = TAU,
      };
      // dump header
      std::ofstream out(out_path);
      if (!out.is_open()) {
        throw std::runtime_error("Could not open output file: " + out_path);
      }
      out << std::setprecision(PRECISION);
      write_sfm_traj_header(out);

      // untill they reach the desired tf, step and dump
      // for left, the target is right initial position
      std::pair<double, double> target_left = {pair.right.x, pair.right.y};

      // for right, the target is left initial position
      std::pair<double, double> target_right = {pair.left.x, pair.left.y};

      for (int i = 0; i < tf; i += dt) {
        Step step = sfm_step(pair, dt, i, target_left, target_right);
        write_sfm_traj_step(out, pair, i);
      }

    } else if (program.get("--type") == "cpm") {
      throw std::invalid_argument("Model CPM not implemented");
    }
  } catch (const std::exception &err) {
    std::cerr << "error: " << err.what() << '\n';
    return 1;
  }
  return 0;
}