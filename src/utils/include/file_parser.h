#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct InitialPositions {
  double particle_left_x;
  double particle_left_y;
  double particle_right_x;
  double particle_right_y;
};
struct InitialSpeeds {
  double particle_left_x;
  double particle_left_y;
  double particle_right_x;
  double particle_right_y;
};
inline InitialPositions parse_initial_positions(const std::string &path,
                                                int left_id, int right_id) {
  std::ifstream file(path);
  if (!file.is_open()) {
    throw std::runtime_error("Could not open file: " + path);
  }

  InitialPositions ret{};
  bool found_left = false;
  bool found_right = false;
  std::string line;

  while (std::getline(file, line)) {
    if (line.empty() || line[0] == '#') {
      continue; // skip comments and blank lines
    }

    std::istringstream iss(line);
    int id, frame, marker;
    double x, y;
    if (!(iss >> id >> frame >> x >> y >> marker)) {
      continue; // malformed line
    }

    if (id == left_id && !found_left) {
      ret.particle_left_x = x;
      ret.particle_left_y = y;
      found_left = true;
    } else if (id == right_id && !found_right) {
      ret.particle_right_x = x;
      ret.particle_right_y = y;
      found_right = true;
    }

    if (found_left && found_right) {
      return ret;
    }
  }

  throw std::runtime_error("Could not find both particles (ids " +
                           std::to_string(left_id) + " and " +
                           std::to_string(right_id) + ") in " + path);
}

struct SpeedRow {
  int test_num;
  int particle_left;
  int particle_right;
  double particle_left_speed;
  double particle_right_speed;
};

struct FileRow {
  int a;
  int b;
  double c;
};

inline double parse_final_time(const std::string &path_str, int num) {
  std::ifstream file(path_str);
  if (!file.is_open()) {
    throw std::runtime_error("Could not open file: " + path_str);
  }
  std::string line;
  int num_file;
  double tf;
  while (std::getline(file, line)) {
    std::istringstream iss(line);
    if (!(iss >> num_file >> tf)) {
      continue;
    }
    if (num_file == num) {
      return tf;
    }
  }
  return (-1.0);
}

inline SpeedRow read_speed(const std::string &path, int num) {
  std::ifstream file(path);
  if (!file.is_open()) {
    throw std::runtime_error("Could not open file: " + path);
  }

  SpeedRow ret;
  ret.test_num = num;
  std::string line;
  bool found1 = false;

  while (std::getline(file, line)) {
    std::istringstream iss(line);
    FileRow r;
    if (!(iss >> r.a >> r.b >> r.c)) {
      continue;
    }

    if (r.a != num) {
      if (found1)
        break; // past the block for num
      continue;
    }

    if (!found1) {
      ret.particle_left = r.b;
      ret.particle_left_speed = r.c;
      found1 = true;
    } else {
      ret.particle_right = r.b;
      ret.particle_right_speed = r.c;
      return ret;
    }
  }

  throw std::runtime_error("Expected two lines starting with " +
                           std::to_string(num));
}

inline int parse_test_num(const std::string &path_str) {
  std::filesystem::path p(path_str);
  std::string stem = p.stem().string();

  const std::string prefix = "prueba";
  if (stem.rfind(prefix, 0) != 0) {
    throw std::runtime_error("Unexpected file name: " + stem);
  }
  return std::stoi(stem.substr(prefix.size()));
}

inline InitialSpeeds parse_initial_speeds(const std::string &path, int left_id,
                                          int right_id, int run_num) {
  std::ifstream file(path);
  if (!file.is_open()) {
    throw std::runtime_error("Could not open file: " + path);
  }

  InitialSpeeds ret{};
  bool found_left = false;
  bool found_right = false;
  std::string line;

  while (std::getline(file, line)) {
    if (line.empty() || line[0] == '#') {
      continue; // skip comments and blank lines
    }

    std::istringstream iss(line);
    int num, id;
    double vx, vy;
    if (!(iss >> num >> id >> vx >> vy)) {
      continue; // malformed line
    }

    if (id == left_id && !found_left && num == run_num) {
      ret.particle_left_x = vx;
      ret.particle_left_y = vy;
      found_left = true;
    } else if (id == right_id && !found_right && num == run_num) {
      ret.particle_right_x = vx;
      ret.particle_right_y = vy;
      found_right = true;
    }

    if (found_left && found_right) {
      return ret;
    }
  }

  throw std::runtime_error("Could not find both particles (ids " +
                           std::to_string(left_id) + " and " +
                           std::to_string(right_id) + ") in " + path);
}