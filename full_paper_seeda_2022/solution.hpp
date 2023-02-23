#include "problem.hpp"
#include "global.hpp"
#include <random>
#include <chrono>
#include <queue>
using namespace std;
using namespace std::chrono;


class Solution
{
    private:
        Problem *problem;
        map <int,vector <int>> periodwise_solution;
        map <int,vector <int>> roomwise_solution;
        map <int,ERSol> solution_set;
        uniform_int_distribution <int> random_event;
        int cost;

    public:
        Solution(Problem *p);
        ~Solution();

        // Solution set
        void customize_solution(map <int,pair <int,int>> &new_solution_set);

        // Operations that determine each operator
        bool can_be_moved(const int &event,const int &period,const vector <int> &excluded);
        bool room_availability(const int &event_id,const int &room_id,const vector <int> &excluded={});

        // Operators
        map <int,pair <int,int>> transfer_event();
        map <int,pair <int,int>> swap_events();
        map <int,pair <int,int>> kempe_chain();
        map <int,pair <int,int>> regroup();
        map <int,pair <int,int>> perturbation();

        // Cost calculation
        int compute_cost();
        int compute_partial_cost();
};