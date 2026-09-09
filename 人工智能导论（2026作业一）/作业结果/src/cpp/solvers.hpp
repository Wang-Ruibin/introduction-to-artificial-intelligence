#pragma once
#include "tsp.hpp"
#include <cstdint>
namespace tsp {
Result SolveGeneticAlgorithm(const Matrix&, std::uint64_t seed = 2026, int population_size = 200,
                             int generations = 200000, double mutation_rate = 0.25,
                             double time_budget_seconds = 15.0);
Result SolveAntColony(const Matrix&, std::uint64_t seed = 2026, int ants = 0, int iterations = 200000,
                      double alpha = 1.0, double beta = 3.0, double evaporation = 0.20,
                      double time_budget_seconds = 15.0);
}
