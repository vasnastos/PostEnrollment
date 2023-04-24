#include "hopcroft_karp.h"

BipGraph::BipGraph(Problem *p,map <int,int> &potential_period_solutions):problem(p),solution(potential_period_solutions)
{
    for(auto &[event_id,period_id]:potential_period_solutions)
    {
        this->events.emplace_back(event_id);
        this->adj[event_id]=this->problem->event_available_rooms[event_id];
    }

    this->pair_event.resize(this->events.size()+1);
    this->pair_room.resize(this->problem->R+1);
    this->dist.resize(this->problem->R+1);

    fill(this->pair_event.begin(),this->pair_event.end(),NIL);
    fill(this->pair_room.begin(),this->pair_room.end(),NIL);
}


bool BipGraph::dfs()
{

}

bool BipGraph::bfs()
{

}

int BipGraph::hocroft_karp()
{
    int result=0;
}
