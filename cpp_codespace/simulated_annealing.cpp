#include "simulated_annealing.h"

SimulatedAnnealing::SimulatedAnnealing(Solution &asolution):solution(&asolution) {}
SimulatedAnnealing::~SimulatedAnnealing() {}

void SimulatedAnnealing::solve()
{
    int temperature=1000;
    double alpha=0.9999;
    double start_temperature=1000;

    while(true)
    {
        // To be filled
    }
}