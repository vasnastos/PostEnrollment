#include "simulated_annealing.hpp"

SimulatedAnnealing::SimulatedAnnealing(Solution *solution_obj):solution(solution_obj) {}

SimulatedAnnealing::~SimulatedAnnealing() {}

void SimulatedAnnealing::solve(size_t elapsed_time)
{
    double temperature=1000.0;
    auto start_timer=high_resolution_clock::now();
    while(true)
    {
        // execute simulated annealing
    }

}

map <int,Sol> SimulatedAnnealing::get_best_solution()const
{
    return this->best_solution;
}