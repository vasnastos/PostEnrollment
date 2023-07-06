#include "solution.hpp"

class SimulatedAnnealing
{
    private:
        Solution *solution;
        map <int,Sol> best_solution;
        double start_temperature;
        double alpha;
        double best_cost;
    public:
        SimulatedAnnealing(Solution *solution_obj);
        ~SimulatedAnnealing();

        void solve(size_t elapsed_time);

        map <int,Sol> get_best_solution()const;
};