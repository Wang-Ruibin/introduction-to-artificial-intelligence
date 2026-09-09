#include "tsp.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
namespace tsp {
Instance LoadTsplib(const std::string& path) {
  std::ifstream input(path); if (!input) throw std::runtime_error("Cannot open: " + path);
  Instance data; std::string line; bool reading = false;
  while (std::getline(input, line)) {
    if (line.rfind("NAME", 0) == 0) { auto p = line.find(':'); data.name = line.substr(p == std::string::npos ? 4 : p + 1); data.name.erase(0, data.name.find_first_not_of(" \t")); data.name.erase(data.name.find_last_not_of(" \t\r") + 1); }
    else if (line.find("NODE_COORD_SECTION") != std::string::npos) reading = true;
    else if (line.find("EOF") != std::string::npos) break;
    else if (reading) { std::istringstream row(line); int id; Point p; if (row >> id >> p.x >> p.y) data.coordinates.push_back(p); }
  }
  if (data.coordinates.empty()) throw std::runtime_error("No coordinates: " + path);
  int n = static_cast<int>(data.coordinates.size()); data.distances.assign(n, std::vector<std::int64_t>(n));
  for (int i = 0; i < n; ++i) for (int j = i + 1; j < n; ++j) {
    double dx = data.coordinates[i].x - data.coordinates[j].x, dy = data.coordinates[i].y - data.coordinates[j].y;
    auto d = static_cast<std::int64_t>(std::floor(std::sqrt(dx*dx + dy*dy) + 0.5)); data.distances[i][j] = data.distances[j][i] = d;
  }
  return data;
}
std::int64_t TourLength(const std::vector<int>& tour, const Matrix& d) {
  std::int64_t total = 0; for (std::size_t i = 0; i < tour.size(); ++i) total += d[tour[i]][tour[(i+1)%tour.size()]]; return total;
}
std::vector<int> NearestNeighbor(int start, const Matrix& d) {
  int n = static_cast<int>(d.size()); std::vector<bool> seen(n); std::vector<int> tour{start}; seen[start] = true;
  while (static_cast<int>(tour.size()) < n) { int current = tour.back(), best = -1; for (int node=0; node<n; ++node) if (!seen[node] && (best<0 || d[current][node]<d[current][best])) best=node; seen[best]=true; tour.push_back(best); }
  return tour;
}
std::vector<int> TwoOpt(std::vector<int> tour, const Matrix& d, int passes) {
  int n=static_cast<int>(tour.size());
  for(int pass=0; pass<passes; ++pass){ bool improved=false; for(int i=0;i<n-1;++i){ int a=tour[i],b=tour[(i+1)%n],upper=i? n:n-1; for(int k=i+2;k<upper;++k){int c=tour[k],e=tour[(k+1)%n]; if(d[a][c]+d[b][e]<d[a][b]+d[c][e]){std::reverse(tour.begin()+i+1,tour.begin()+k+1); improved=true;}}} if(!improved) break; }
  return tour;
}
std::vector<int> OrOpt(std::vector<int> tour, const Matrix& d, int max_passes) {
  const int n = static_cast<int>(tour.size());
  for (int pass = 0; pass < max_passes; ++pass) {
    bool improved = false;
restart_scan:
    for (int len = 1; len <= 3 && len < n; ++len) {
      for (int a = 0; a + len <= n; ++a) {
        const int b = a + len - 1;             // move segment tour[a..b]
        const int x = (a - 1 + n) % n;         // predecessor index of the segment
        const int y = (b + 1) % n;             // successor index of the segment
        for (int p = 0; p < n; ++p) {          // insertion point between tour[p] and tour[p+1]
          if (p >= a && p <= b) continue;      // inside the segment itself
          if (p == x) continue;                // original position, no-op
          const int q = (p + 1) % n;
          const std::int64_t before = d[tour[x]][tour[a]] + d[tour[b]][tour[y]] + d[tour[p]][tour[q]];
          const std::int64_t forward = d[tour[x]][tour[y]] + d[tour[p]][tour[a]] + d[tour[b]][tour[q]];
          const std::int64_t reverse = d[tour[x]][tour[y]] + d[tour[p]][tour[b]] + d[tour[a]][tour[q]];
          if (forward >= before && (len == 1 || reverse >= before)) continue;
          const bool flipped = len > 1 && reverse < forward;
          std::vector<int> segment(tour.begin() + a, tour.begin() + b + 1);
          if (flipped) std::reverse(segment.begin(), segment.end());
          std::vector<int> next;
          next.reserve(n);
          for (int k = 0; k < n; ++k) if (k < a || k > b) next.push_back(tour[k]);
          const int at = (p < a) ? p + 1 : p - len + 1;  // index after tour[p] in `next`
          next.insert(next.begin() + at, segment.begin(), segment.end());
          tour = std::move(next);
          improved = true;
          goto restart_scan;
        }
      }
    }
    if (!improved) break;
  }
  return tour;
}
std::vector<int> LocalSearch(std::vector<int> tour, const Matrix& d) {
  std::vector<int> current = std::move(tour);
  for (;;) {
    std::vector<int> next = OrOpt(TwoOpt(current, d), d);
    if (next == current) return next;
    current = std::move(next);
  }
}
std::vector<int> CanonicalTour(const std::vector<int>& tour) {
  auto zero=std::find(tour.begin(),tour.end(),0); std::vector<int> f; f.insert(f.end(),zero,tour.end()); f.insert(f.end(),tour.begin(),zero); std::vector<int> r{f.front()}; r.insert(r.end(),f.rbegin(),f.rend()-1); return std::min(f,r);
}
void WriteResultJson(const Result& r, const std::string& path) {
  std::ofstream out(path); if(!out) throw std::runtime_error("Cannot write: "+path); out<<std::fixed<<std::setprecision(9);
  out<<"{\n  \"algorithm\": \""<<r.algorithm<<"\",\n  \"language\": \"C++\",\n  \"distance\": "<<r.distance<<",\n  \"runtime_seconds\": "<<r.runtime_seconds<<",\n  \"tour\": [";
  for(std::size_t i=0;i<r.tour.size();++i) {
    out<<(i?", ":"")<<r.tour[i];
  }
  out<<"],\n  \"parameters\": "<<r.parameters_json<<",\n  \"progress\": [\n";
  for(std::size_t i=0;i<r.progress.size();++i){auto&p=r.progress[i]; out<<"    {\"step\": "<<p.step<<", \"distance\": "<<p.distance<<", \"time_seconds\": "<<p.time_seconds<<"}"<<(i+1==r.progress.size()?"\n":",\n");} out<<"  ]\n}\n";
}
}
