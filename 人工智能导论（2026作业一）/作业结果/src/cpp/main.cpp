#include "solvers.hpp"
#include "tsp.hpp"
#include <cstdlib>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
int main(int argc, char* argv[]) {
  if (argc != 4 && argc != 5) {
    std::cerr << "Usage: tsp_metaheuristics <instance.tsp> <ga|aco> <result.json> [time_budget_seconds]\n";
    return 2;
  }
  try {
    auto instance = tsp::LoadTsplib(argv[1]);
    const std::string algorithm = argv[2];
    const double budget = (argc == 5) ? std::stod(argv[4]) : 15.0;
    tsp::Result result;
    if (algorithm == "ga")
      result = tsp::SolveGeneticAlgorithm(instance.distances, 2026, 200, 200000, 0.25, budget);
    else if (algorithm == "aco")
      result = tsp::SolveAntColony(instance.distances, 2026, 0, 200000, 1.0, 3.0, 0.20, budget);
    else
      throw std::runtime_error("Unknown algorithm: " + algorithm);
    tsp::WriteResultJson(result, argv[3]);
    std::cout << instance.name << " / " << result.algorithm << ": distance=" << result.distance
              << ", runtime=" << result.runtime_seconds << "s\n";
  } catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << '\n';
    return 1;
  }
}
