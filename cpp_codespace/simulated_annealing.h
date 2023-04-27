#pragma once
#include "solution.h"
#include "tabu_search.h"
#include <cmath>

class SimulatedAnnealing
{
    private:
        Solution *solution;
    public:
        SimulatedAnnealing(Solution &asolution);
        ~SimulatedAnnealing();

        void preprocessing();

        void solve(int timesol);
        void SAR();
};