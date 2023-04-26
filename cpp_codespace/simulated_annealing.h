#include "solution.h"
#include <cmath>

class SimulatedAnnealing
{
    private:
        Solution *solution;
    public:
        SimulatedAnnealing(Solution &asolution);
        ~SimulatedAnnealing();

        void solve(int timesol);
        void SAR();
};