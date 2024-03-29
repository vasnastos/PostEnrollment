#include "problem.hpp"
#include <random>
#include <chrono>
#include <stack>
using namespace std::chrono;

struct Sol
{
    int period;
    int room;
    Sol();
    Sol(int _p,int _r);
};

enum class OPERATOR
{
    TRANSFER,
    SWAP,
    KEMPE,
    DOUBLE_KEMPE,
    KICK,
    DOUBLE_KICK,
    NONE
};

class Solution
{
    private:
        Problem *problem;
        map <int,Sol> schedule_set;
        map <int,vector <int>> periodwise_solutions;
        map <int,vector <int>> roomwise_solutions;
        map <int,Sol> memory;
        map <OPERATOR,int> move_usage;


        // secondary attributes
        uniform_int_distribution <int> random_event;
        vector <int> last_periods_per_day;

        void build_double_kempe_chain(const int &event_id,map <int,Sol> &moves);

        // For the solution procedure
        OPERATOR move_name;

    public:
        mt19937 eng;

        Solution(Problem *new_problem_instance);

        size_t compute_cost();
        size_t compute_daily_cost(int day);
        string get_named_move();

        void reposition(map <int,Sol> &moves);
        void rollback();   
        void set_solution(map <int,Sol> &moves); 

        void schedule(const int &pevent,const int &room,const int &period);
        void unschedule(const int &event);
        bool can_be_moved(const int &event_id,const int &period_id,const vector <int> &excluded={});
        bool room_availability(const int &event_id,const int &period,const int &room,const vector <int> &excluded={});

        int select_random_event();
        int select_random_neighbor(const int &neighbor_id);
        bool room_selection(map <int,Sol> &moves);
        Problem* get_problem()const;

        // Operators
        map <int,Sol> select_numbered_operator(OPERATOR op);
        map <int,Sol> select_random_operator();
        map <int,Sol> select_operator_based_on_precedence();
        map <int,Sol> select_operator();

        map <int,Sol> transfer();
        map <int,Sol> swap();
        map <int,Sol> kempe_chain();
        map <int,Sol> double_kempe_chain();
        map <int,Sol> kick_event();
        map <int,Sol> double_kick_event();

        map <int,Sol> get_schedule();
};