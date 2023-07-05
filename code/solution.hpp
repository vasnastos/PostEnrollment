#include "problem.hpp"
#include <random>
#include <chrono>
#include <stack>
using namespace std::chrono;

struct Sol
{
    int period;
    int room;
    Sol(int _p,int _r):period(_p),room(_r) {}
};

class Solution
{
    private:
        Problem *problem;
        map <int,Sol> schedule_set;
        map <int,vector <int>> periodwise_solutions;
        map <int,vector <int>> roomwise_solutions;
        map <int,Sol> memory;


        // secondary attributes
        uniform_int_distribution <int> random_event;
        vector <int> last_periods_per_day;

        void build_double_kempe_chain(const int &event_id,map <int,Sol> &moves);

    public:
        Solution(Problem *new_problem_instance);

        size_t compute_cost();
        size_t compute_daily_cost();

        void reposition(map <int,Sol> &moves);
        void rollback();    

        void schedule(const int &pevent,const int &room,const int &period);
        void unschedule(const int &event);
        bool can_be_moved(const int &event_id,const int &period_id,const vector <int> &excluded={});
        bool room_availability(const int &event_id,const int &period,const int &room,const vector <int> &excluded={});

        int select_random_event();
        bool room_selection(map <int,Sol> &moves);

        Problem* get_problem()const;

        // Operators
        map <int,Sol> transfer();
        map <int,Sol> swap();
        map <int,Sol> kempe_chain();
        map <int,Sol> double_kempe_chain();
};