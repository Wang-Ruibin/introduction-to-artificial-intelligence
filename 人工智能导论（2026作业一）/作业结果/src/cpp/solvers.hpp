#pragma once
#include "tsp.hpp"
#include <cstdint>
namespace tsp {
Result SolveGeneticAlgorithm(const Matrix&, std::uint64_t seed = 2026, int population_size = 160,
                             int generations = 500, double mutation_rate = 0.2);
Result SolveAntColony(const Matrix&, std::uint64_t seed = 2026, int ants = 48, int iterations = 220,
                      double alpha = 1.0, double beta = 4.0, double evaporation = 0.35);
}
