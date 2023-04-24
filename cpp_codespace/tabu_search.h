#pragma once
#include "problem.h"
#include <iostream>
#include <iostream>
#include <vector>

class TabuInit
{
    private:
        int clashsum;
        Problem *problem;
        vector <int> unplaced;
        vector <int> conflicted_events;
        vector <int> tabu_list;
        map <int,int> period_solution;
        map <int,int> room_solution;
        map <int,int> memory;

    public:
        TabuInit(Problem *p);
        void create_unassigned();
        void remove(int &event_id);
        void rollback(int &event_id);
        void find_conflicting_events(int &event_id,int &period_id);
        bool tabu(const int &event_id);
        int objective();
        
        void perturb();
        void tssp(int timesol);

        // Room assignment
        void maximal_room_matching();
        void match(const int &event_id);

        // Operators for room sol

};