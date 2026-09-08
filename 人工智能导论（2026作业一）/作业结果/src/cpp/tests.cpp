#include "tsp.hpp"
#include <cassert>
#include <iostream>
int main(){const tsp::Matrix d{{0,1,3},{1,0,2},{3,2,0}};assert(tsp::TourLength({0,1,2},d)==6);assert((tsp::CanonicalTour({2,1,0})==std::vector<int>{0,1,2}));std::cout<<"C++ utility tests passed\n";}
