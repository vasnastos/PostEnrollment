#include "problem.h"

struct Sol
{
    int period;
    int room;
    Sol(int p_,int r_);
    Sol(const Sol &sln);
};

class Solution
{
    private:
        Problem *problem;
        map <int,Sol> solution_set;
        map <int,vector <int>> periodwise_solutions;
        map <int,vector <int>> roomwise_solutions;
        map <int,Sol> memory;

        uniform_int_distribution <int> rand_event;
        mt19937 mt;
    public:
        Solution(string filename);
        ~Solution();

        int schedule(const int &event_id,const int &room_id,const int &period_id);
        int unschedule(const int &event_id);

        int compute_cost();
        int compute_daily_cost(int day);

        bool can_be_moved(const int &event,const int &period,const vector <int> &excluded={});
        bool is_room_available(const int &room_id,const int &period_id);

        void reposition(const int &event,const int &room,const int &period_id);
        void reposition(map <int,Sol> &moves);
        void rollback();

        map <int,Sol> transfer_event(const int &event);
        map <int,Sol> swap_events(const int &event);
        map <int,Sol> kempe_chain(const int &event);
        map <int,Sol> kick(const int &event);
        map <int,Sol> double_kick(const int &event);
};