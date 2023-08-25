#include "solution.hpp"

class TSSP
{
    private:
        Solution *solution;
        size_t elapsed_time;
        vector <int> unassigned_events;
        map <int,Sol> best_solution;
        map <int,Sol> current_solution;
        vector <map <int,int>> tabulist;
        int best_cost;

        std::chrono::time_point<chrono::high_resolution_clock> start_timer;

        bool define_tabu(vector <int> &confe);
        double objective_function(vector <int> &unplaced_events);
        vector <int> sampling(vector <int> &unplaced_events);
        vector <int> conflicting_events(const int &event_id,const int &period_id);
        bool tssp_elapsed();


    public:
        TSSP(Solution *sol_item,size_t solution_time_in_seconds);
        void solve();
        map <int,Sol> get_best_solution();
};