#include "hopcroft_karp.h"

BipGraph::BipGraph(Problem *p,map <int,int> &potential_period_solutions):problem(p),period_solution(potential_period_solutions)
{
    for(auto &[event_id,period_id]:potential_period_solutions)
    {
        this->events.emplace_back(event_id);
        for(auto &x:this->problem->event_available_rooms[event_id])
        {
            this->adj[event_id].emplace_back(this->events.size()+1+x);    
        }
    }

    this->pair_event.resize(this->events.size());
    this->pair_room.resize(this->problem->R);

    fill(this->pair_event.begin(),this->pair_event.end(),NIL);
    fill(this->pair_room.begin(),this->pair_room.end(),NIL);

    this->number_of_nodes=this->events.size()+1+this->problem->R;
    this->dist.resize(this->number_of_nodes);
}

bool BipGraph::dfs(const int &event_id)
{
    if(event_id!=NIL)
    {
        for(auto &room_id:this->adj[event_id])
        {
            if(this->dist[this->pair_room[room_id-(this->events.size()+1)]]==this->dist[event_id]+1)
            {
                if(this->dfs(this->pair_room[room_id-(this->events.size()+1)]))
                {
                    
                    this->pair_room[room_id-(this->events.size()+1)]=event_id;
                    this->pair_event[event_id]=room_id;
                    return true;
                }
            }
        }

        this->dist[event_id]=INF;
        return false;
    }
    return true;
}

bool BipGraph::bfs()
{
    queue <int> q;

    for(int eid=0;eid<this->problem->E;eid++)
    {
        if(pair_event[eid]==NIL)
        {
            dist[eid]=0;
            q.push(eid);
        }
        else
            dist[eid]=NIL;
    }

    int event_id;
    while(!q.empty())
    {
        event_id=q.front();
        q.pop();

        if(this->dist[event_id]<this->dist[NIL])
        {
            for(auto &room_id:this->adj[event_id])
            {
                if(dist[this->pair_room[room_id-(this->events.size()+1)]]==INF)
                {
                    if(this->can_be_moved(event_id,room_id))
                    {
                        this->dist[this->pair_room[room_id-this->events.size()]]=this->dist[event_id]+1;
                        q.push(this->dist[this->pair_room[room_id-(this->events.size()+1)]]);
                    }
                }
            }
        }
    }

    return (this->dist[NIL]!=INF);
}

int BipGraph::hocroft_karp()
{
    int result=0;
    while(this->bfs())
    {
        for(int event_id=1,m=this->events.size();event_id<m;event_id++)
        {
            if(this->pair_event[event_id]=NIL && this->dfs(event_id))
            {
                result++;
            }
        }
    }
    return result;
}

void BipGraph::place(const int &event_id,const int &room_id)
{
    int transformed_event_id=this->events[event_id-1];
    int transformed_room_id=room_id-(this->events.size()+1);

    this->room_solution[transformed_event_id]=transformed_room_id;
}

bool BipGraph::can_be_moved(int &event_id,int &room_id)
{
    int transformed_event_id=this->events[event_id-1];
    int transformed_room_id=room_id-(this->events.size()+1);

    for(auto &[event_id2,period_id]:this->period_solution)
    {
        if(event_id==event_id2) continue;
        if(this->period_solution[event_id]==this->period_solution[event_id2])
        {
            if(this->room_solution[event_id2]==room_id)
            {
                return false;
            }
        }
    }

    return true;
}

map <int,int> BipGraph::get_solution()
{
    return this->room_solution;
}
