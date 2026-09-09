#pragma once
#include <cstdint>
#include <string>
#include <vector>
namespace tsp {
using Matrix = std::vector<std::vector<std::int64_t>>;
struct Point { double x{}, y{}; };
struct Instance { std::string name; std::vector<Point> coordinates; Matrix distances; };
struct ProgressPoint { int step{}; std::int64_t distance{}; double time_seconds{}; };
struct Result {
  std::string algorithm; std::vector<int> tour; std::int64_t distance{}; double runtime_seconds{};
  std::vector<ProgressPoint> progress; std::string parameters_json;
};
Instance LoadTsplib(const std::string& path);
std::int64_t TourLength(const std::vector<int>& tour, const Matrix& distances);
std::vector<int> NearestNeighbor(int start, const Matrix& distances);
std::vector<int> TwoOpt(std::vector<int> tour, const Matrix& distances, int max_passes = 20);
std::vector<int> OrOpt(std::vector<int> tour, const Matrix& distances, int max_passes = 20);
std::vector<int> LocalSearch(std::vector<int> tour, const Matrix& distances);
std::vector<int> CanonicalTour(const std::vector<int>& tour);
void WriteResultJson(const Result& result, const std::string& path);
}
