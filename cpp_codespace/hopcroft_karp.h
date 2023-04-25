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

    map <int,int> period_solution;
    map <int,int> room_solution;

    int number_of_nodes;
    
public:
    BipGraph(Problem *p,map <int,int> &potential_period_solutions);

    bool dfs(const int &event_id);
    bool bfs();
    int hocroft_karp();

    void place(const int &event_id,const int &room_id);
    bool can_be_moved(int &event_id,int &room_id);

    map <int,int> get_solution();
};
