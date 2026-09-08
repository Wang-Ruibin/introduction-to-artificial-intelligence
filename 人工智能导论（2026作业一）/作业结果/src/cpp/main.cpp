#include "solvers.hpp"
#include "tsp.hpp"
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
int main(int argc,char*argv[]){if(argc!=4){std::cerr<<"Usage: tsp_metaheuristics <instance.tsp> <ga|aco> <result.json>\n";return 2;}try{auto instance=tsp::LoadTsplib(argv[1]);std::string algorithm=argv[2];tsp::Result result;if(algorithm=="ga")result=tsp::SolveGeneticAlgorithm(instance.distances);else if(algorithm=="aco")result=tsp::SolveAntColony(instance.distances);else throw std::runtime_error("Unknown algorithm: "+algorithm);tsp::WriteResultJson(result,argv[3]);std::cout<<instance.name<<" / "<<result.algorithm<<": distance="<<result.distance<<", runtime="<<result.runtime_seconds<<"s\n";}catch(const std::exception&e){std::cerr<<"Error: "<<e.what()<<'\n';return 1;}}
