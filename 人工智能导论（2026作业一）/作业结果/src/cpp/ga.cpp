#include "solvers.hpp"
#include <algorithm>
#include <chrono>
#include <limits>
#include <numeric>
#include <random>
#include <sstream>

namespace tsp {
namespace {

using Clock = std::chrono::steady_clock;

double Sec(Clock::time_point start) {
  return std::chrono::duration<double>(Clock::now() - start).count();
}

// Order crossover (OX): copy a slice of parent a, then fill the remaining cities
// in the order they appear in parent b.
std::vector<int> Crossover(const std::vector<int>& a, const std::vector<int>& b, std::mt19937_64& rng) {
  const int n = static_cast<int>(a.size());
  std::uniform_int_distribution<int> pick(0, n - 1);
  int l = pick(rng), r = pick(rng);
  if (l > r) std::swap(l, r);
  if (l == r) r = std::min(n, l + 1);
  std::vector<int> child(n, -1);
  std::vector<bool> used(n);
  for (int i = l; i < r; ++i) used[child[i] = a[i]] = true;
  int at = r % n;
  for (int k = 0; k < n; ++k) {
    int x = b[(r + k) % n];
    if (!used[x]) { child[at] = x; at = (at + 1) % n; }
  }
  return child;
}

// Double-bridge perturbation: a 4-opt move that cannot be undone by 2-opt,
// used to kick tours out of the current local-optimum basin.
std::vector<int> DoubleBridge(const std::vector<int>& tour, std::mt19937_64& rng) {
  const int n = static_cast<int>(tour.size());
  if (n < 8) return tour;
  std::uniform_int_distribution<int> pick_a(1, n - 4);
  const int a = pick_a(rng);
  std::uniform_int_distribution<int> pick_b(a + 1, n - 3);
  const int b = pick_b(rng);
  std::uniform_int_distribution<int> pick_c(b + 1, n - 2);
  const int c = pick_c(rng);
  std::vector<int> out;
  out.reserve(n);
  out.insert(out.end(), tour.begin(), tour.begin() + a);
  out.insert(out.end(), tour.begin() + b, tour.begin() + c);
  out.insert(out.end(), tour.begin() + a, tour.begin() + b);
  out.insert(out.end(), tour.begin() + c, tour.end());
  return out;
}

}

// Memetic genetic algorithm: every child is refined by 2-opt + or-opt local
// search, and the population is reseeded with kicked copies of the global best
// and fresh random local optima whenever it stagnates.
Result SolveGeneticAlgorithm(const Matrix& d, std::uint64_t seed, int population_size,
                             int generations, double mutation_rate, double time_budget_seconds) {
  auto start = Clock::now();
  const int n = static_cast<int>(d.size());
  const int size = std::max(20, population_size);
  std::mt19937_64 rng(seed);

  std::vector<std::vector<int>> pop;
  pop.reserve(size);
  for (int i = 0; i < n && static_cast<int>(pop.size()) < size; ++i)
    pop.push_back(LocalSearch(NearestNeighbor(i, d), d));
  {
    std::vector<int> base(n);
    std::iota(base.begin(), base.end(), 0);
    while (static_cast<int>(pop.size()) < size) {
      std::shuffle(base.begin(), base.end(), rng);
      pop.push_back(LocalSearch(base, d));
    }
  }

  std::vector<int> best;
  std::int64_t best_len = std::numeric_limits<std::int64_t>::max();
  std::vector<ProgressPoint> progress;
  std::uniform_real_distribution<double> chance(0, 1);
  std::uniform_int_distribution<int> pos(0, n - 1);
  const int elites = std::max(2, size / 20);
  const int restart_stall = 120;
  const double min_run_seconds = 2.0;   // never stop before this
  const double patience_seconds = 5.0;  // stop after this long without improvement
  double last_improve = 0.0;
  int stall = 0;
  int gen = 0;

  for (; gen < generations; ++gen) {
    const double elapsed = Sec(start);
    if (elapsed >= time_budget_seconds) break;

    std::vector<std::int64_t> len(size);
    for (int i = 0; i < size; ++i) len[i] = TourLength(pop[i], d);
    std::vector<int> order(size);
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](int a, int b) { return len[a] < len[b]; });
    bool improved_now = len[order[0]] < best_len;
    if (improved_now) {
      best_len = len[order[0]];
      best = pop[order[0]];
      last_improve = elapsed;
      stall = 0;
    } else {
      ++stall;
    }
    if (improved_now || gen % 10 == 0) progress.push_back({gen, best_len, elapsed});
    if (elapsed >= min_run_seconds && elapsed - last_improve >= patience_seconds) break;

    auto tournament = [&]() -> const std::vector<int>& {
      std::uniform_int_distribution<int> candidate(0, size - 1);
      int win = candidate(rng);
      for (int k = 1; k < 4; ++k) {
        int x = candidate(rng);
        if (len[x] < len[win]) win = x;
      }
      return pop[win];
    };

    std::vector<std::vector<int>> next;
    next.reserve(size);
    for (int i = 0; i < elites; ++i) next.push_back(pop[order[i]]);

    if (stall >= restart_stall) {
      const int kept = std::max(elites, size / 10);
      for (int i = elites; i < kept; ++i) next.push_back(pop[order[i]]);
      while (static_cast<int>(next.size()) < size) {
        if (chance(rng) < 0.5) {
          next.push_back(LocalSearch(DoubleBridge(best, rng), d));
        } else {
          std::vector<int> base(n);
          std::iota(base.begin(), base.end(), 0);
          std::shuffle(base.begin(), base.end(), rng);
          next.push_back(LocalSearch(base, d));
        }
      }
      stall = 0;
    } else {
      while (static_cast<int>(next.size()) < size) {
        std::vector<int> child = Crossover(tournament(), tournament(), rng);
        if (chance(rng) < mutation_rate) {
          int l = pos(rng), r = pos(rng);
          if (l > r) std::swap(l, r);
          std::reverse(child.begin() + l, child.begin() + r + 1);
        }
        if (chance(rng) < 0.05) child = DoubleBridge(child, rng);
        next.push_back(LocalSearch(std::move(child), d));
      }
    }
    pop = std::move(next);
  }

  best = LocalSearch(std::move(best), d);
  best_len = TourLength(best, d);
  const double runtime = Sec(start);
  progress.push_back({gen + 1, best_len, runtime});
  std::ostringstream params;
  params << "{\"seed\": " << seed << ", \"population_size\": " << size
         << ", \"generations_cap\": " << generations << ", \"mutation_rate\": " << mutation_rate
         << ", \"local_search\": \"2-opt + or-opt\", \"time_budget_seconds\": " << time_budget_seconds
         << ", \"patience_seconds\": " << patience_seconds << "}";
  return {"GA", CanonicalTour(best), best_len, runtime, std::move(progress), params.str()};
}

}
