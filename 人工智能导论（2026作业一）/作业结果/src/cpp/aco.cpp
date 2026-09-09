#include "solvers.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <numeric>
#include <random>
#include <sstream>

namespace tsp {
namespace {

using Clock = std::chrono::steady_clock;

double Sec(Clock::time_point start) {
  return std::chrono::duration<double>(Clock::now() - start).count();
}

}

// MAX-MIN ant system (Stützle & Hoos): pheromone is bounded to [tau_min,
// tau_max] and only the iteration best (periodically the global best) deposits,
// which prevents premature pheromone lock-in. The best few tours of each
// iteration are refined by 2-opt + or-opt local search before learning, so the
// colony only ever reinforces locally optimal structure.
Result SolveAntColony(const Matrix& d, std::uint64_t seed, int ants, int iterations,
                      double alpha, double beta, double evaporation, double time_budget_seconds) {
  auto start = Clock::now();
  const int n = static_cast<int>(d.size());
  const int colony = ants > 0 ? ants : n;
  std::mt19937_64 rng(seed);

  std::vector<std::vector<double>> pher(n, std::vector<double>(n));
  std::vector<std::vector<double>> eta(n, std::vector<double>(n));
  for (int i = 0; i < n; ++i)
    for (int j = 0; j < n; ++j)
      if (i != j) eta[i][j] = 1.0 / static_cast<double>(d[i][j]);

  auto best = LocalSearch(NearestNeighbor(0, d), d);
  auto best_len = TourLength(best, d);
  double tau_max = 1.0 / (evaporation * static_cast<double>(best_len));
  double tau_min = tau_max / (2.0 * static_cast<double>(n));
  for (auto& row : pher) std::fill(row.begin(), row.end(), tau_max);

  std::vector<ProgressPoint> progress;
  std::vector<double> weights(n);
  const int restart_stall = 120;
  const double min_run_seconds = 2.0;   // never stop before this
  const double patience_seconds = 5.0;  // stop after this long without improvement
  double last_improve = 0.0;
  int stall = 0;
  int iter = 0;

  for (; iter < iterations; ++iter) {
    if (Sec(start) >= time_budget_seconds) break;

    std::vector<std::vector<int>> tours(colony);
    std::vector<std::int64_t> lengths(colony);
    for (int ant = 0; ant < colony; ++ant) {
      std::vector<int>& route = tours[ant];
      route.push_back(ant % n);
      std::vector<bool> seen(n);
      seen[route[0]] = true;
      while (static_cast<int>(route.size()) < n) {
        const int current = route.back();
        double total = 0;
        for (int node = 0; node < n; ++node)
          if (!seen[node]) total += weights[node] = std::pow(pher[current][node], alpha) * std::pow(eta[current][node], beta);
        std::uniform_real_distribution<double> choose(0, total);
        double draw = choose(rng);
        int next = -1;
        for (int node = 0; node < n; ++node)
          if (!seen[node] && (draw -= weights[node]) <= 0) { next = node; break; }
        if (next < 0)
          for (int node = n - 1; node >= 0; --node)
            if (!seen[node]) { next = node; break; }
        route.push_back(next);
        seen[next] = true;
      }
      lengths[ant] = TourLength(route, d);
    }

    std::vector<int> order(colony);
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](int a, int b) { return lengths[a] < lengths[b]; });
    const int refine = std::min(colony, 3);
    for (int rank = 0; rank < refine; ++rank) {
      tours[order[rank]] = LocalSearch(std::move(tours[order[rank]]), d);
      lengths[order[rank]] = TourLength(tours[order[rank]], d);
    }
    int iter_best = 0;
    for (int ant = 1; ant < colony; ++ant)
      if (lengths[ant] < lengths[iter_best]) iter_best = ant;

    bool improved_now = lengths[iter_best] < best_len;
    if (improved_now) {
      best_len = lengths[iter_best];
      best = tours[iter_best];
      last_improve = Sec(start);
      stall = 0;
      tau_max = 1.0 / (evaporation * static_cast<double>(best_len));
      tau_min = tau_max / (2.0 * static_cast<double>(n));
    } else {
      ++stall;
    }

    // Deposit on the iteration best; every 10th iteration learn from the global best instead.
    const std::vector<int>& deposit = ((iter % 10) == 9) ? best : tours[iter_best];
    const double add = 1.0 / static_cast<double>(TourLength(deposit, d));
    for (auto& row : pher)
      for (double& v : row) v *= (1.0 - evaporation);
    for (int i = 0; i < n; ++i) {
      const int a = deposit[i], b = deposit[(i + 1) % n];
      pher[a][b] += add;
      pher[b][a] += add;
    }
    if (stall >= restart_stall) {
      for (auto& row : pher) std::fill(row.begin(), row.end(), tau_max);
      stall = 0;
    }
    for (auto& row : pher)
      for (double& v : row) v = std::clamp(v, tau_min, tau_max);

    if (improved_now || iter % 10 == 0) progress.push_back({iter, best_len, Sec(start)});
    const double now = Sec(start);
    if (now >= min_run_seconds && now - last_improve >= patience_seconds) break;
  }

  best = LocalSearch(std::move(best), d);
  best_len = TourLength(best, d);
  const double runtime = Sec(start);
  progress.push_back({iter + 1, best_len, runtime});
  std::ostringstream params;
  params << "{\"seed\": " << seed << ", \"ants\": " << colony
         << ", \"iterations_cap\": " << iterations << ", \"alpha\": " << alpha
         << ", \"beta\": " << beta << ", \"evaporation\": " << evaporation
         << ", \"variant\": \"MAX-MIN + 2-opt/or-opt\", \"time_budget_seconds\": " << time_budget_seconds
         << ", \"patience_seconds\": " << patience_seconds << "}";
  return {"ACO", CanonicalTour(best), best_len, runtime, std::move(progress), params.str()};
}

}
