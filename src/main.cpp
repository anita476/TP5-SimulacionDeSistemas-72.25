#include <argparse/argparse.hpp>

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

  try {
    program.parse_args(argc, argv);
  } catch (const std::exception &err) {
    std::cerr << err.what() << '\n';
    std::cerr << program;
    return 1;
  }
  try {
    // create the two particles with the initial speed 0

    // untill they reach the desired tf, step
    // print each step

  } catch (const std::exception &err) {
    std::cerr << "error: " << err.what() << '\n';
    return 1;
  }
  return 0;
}