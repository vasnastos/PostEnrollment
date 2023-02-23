#pragma once
#include "problem.hpp"


class SA
{
    private:
        map <int,vector <int>> periods;
    
    public:
        SA(Problem *p);
        ~SA();

        // Heuristic Moves
        map <int,int> transfer_event();
        map <int,int> swap_events();
        map <int,int> kempe_chain();

        // Solve
        void solve();
};