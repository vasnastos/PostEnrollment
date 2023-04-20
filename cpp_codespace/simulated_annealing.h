#include "solution.h"

class SimulatedAnnealing
{
    private:
        Solution *solution;
    public:
        SimulatedAnnealing(Solution &asolution);
        ~SimulatedAnnealing();

        void solve();
};