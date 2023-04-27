#pragma once
#include "problem.h"

class Solution
{
    private:
        Problem *problem;
        map <int,vector <int>> periodwise_solutions;
        map <int,vector <int>> roomwise_solutions;
        map <int,Sol> memory;

        uniform_int_distribution <int> rand_event;

        int tournment_size;

    public:
        mt19937 mt;
        map <int,Sol> solution_set;

        Solution(string filename);
        ~Solution();

        Problem* get_problem();

        int schedule(const int &event_id,const int &room_id,const int &period_id);
        int unschedule(const int &event_id);

        int compute_cost();
        int compute_daily_cost(int day);

        bool can_be_moved(const int &event,const int &period,const vector <int> &excluded={});
        bool is_room_available(const int &event_id,const int &room_id,const int &period_id,const vector <int> &excluded={});

        void reposition(const int &event,const int &room,const int &period_id);
        void reposition(map <int,Sol> &moves);
        void rollback();
        void set_solution(map <int,Sol> &candicate_solution);

        void set_tournment_size(const int &size);
        int get_tournament_size()const;

        // Operators
        int tournament_selection();
        map <int,Sol> transfer_event(const int &event);
        map <int,Sol> swap_events(const int &event);
        map <int,Sol> kempe_chain(const int &event);
        map <int,Sol> kick(const int &event);
        map <int,Sol> double_kick(const int &event);

        map <int,Sol> select_operator(string &move_name);

        void save();
};