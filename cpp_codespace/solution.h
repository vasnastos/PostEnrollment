#include "problem.h"

struct Sol
{
    int period;
    int room;
};

class Solution
{
    private:
        map <int,Sol> solution_set;
        map <int,vector <int>> periodwise_solutions;
        map <int,vector <int>> roomwise_solutions;
    public:
        Solution(string filename);
        ~Solution();

        int schedule(int &event_id,int &period_id,int &room_id);
        int unschedule(int &event_id);

        int compute_cost();
        int compute_daily_cost(int day);
};