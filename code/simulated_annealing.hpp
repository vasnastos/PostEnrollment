#include "solution.hpp"
const string Celsius="°C";

class SimulatedAnnealing
{
    private:
        Solution *solution;
        map <int,Sol> best_solution;
        double start_temperature;
        double freeze_temperature;
        double alpha;
        double best_cost;
        size_t solution_time;

        chrono::time_point<chrono::high_resolution_clock> start_timer;
        bool time_elapsed();

    public:
        SimulatedAnnealing(Solution *solution_obj);
        ~SimulatedAnnealing();

        void solve(size_t elapsed_time);

        map <int,Sol> get_best_solution()const;
};