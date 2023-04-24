#pragma once
#include "problem.h"
#include <vector>
#include <queue>
#define INF INT_MAX
#define NIL 0

class BipGraph
{
private:
    Problem *problem;
    map <int,vector<int>> adj;
    
    vector <int> events;
    vector <int> pair_event;
    vector <int> pair_room;
    vector <int> dist;

    map <int,int> solution;
    map <int,int> room_solution;
    
public:
    BipGraph(Problem *p,map <int,int> &potential_period_solutions);

    bool dfs();
    bool bfs();

    int hocroft_karp();
};
