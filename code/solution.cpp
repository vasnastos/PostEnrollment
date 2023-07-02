#include "solution.hpp"

mt19937 eng(high_resolution_clock::now().time_since_epoch().count());

Solution::Solution(Problem *new_problem_instance):problem(new_problem_instance) {
    this->random_event.param(uniform_int_distribution<int>::param_type(0,new_problem_instance->E));
}


size_t Solution::compute_cost()
{
    size_t total_cost=0;
    size_t consecutive,daily_events;
    vector <int> student_participation_in_periodicals;

    // Calculate single event days and consecutive events cost
    for(int student_id=0;student_id<this->problem->S;student_id++)
    {
        student_participation_in_periodicals.clear();
        for(auto &eid:this->problem->students[student_id])
        {
            student_participation_in_periodicals.emplace_back(this->schedule_set[eid].period);
        }

        for(int day=0;day<this->problem->days;day++)
        {
            consecutive=0;
            daily_events=0;
            for(int period_id=day*this->problem->periods_per_day;period_id<day*this->problem->periods_per_day+this->problem->periods_per_day;period_id++)
            {
                if(find(student_participation_in_periodicals.begin(),student_participation_in_periodicals.end(),period_id)!=student_participation_in_periodicals.end())
                {
                    daily_events++;
                    consecutive++;
                }
                else
                {
                    if(consecutive>2)
                    {
                        total_cost+=(consecutive-2);
                    }
                    consecutive=0;
                }
            }

            if(daily_events==1)
            {
                total_cost++;
            }
            else
            {
                if(consecutive>2)
                {
                    total_cost+=(consecutive-2);
                }

            }
        }
    }

    for(int eid=0;eid<this->problem->E;eid++)
    {
        if(find(this->last_periods_per_day.begin(),this->last_periods_per_day.end(),this->schedule_set[eid].period)!=this->last_periods_per_day.end())
        {
            total_cost+=this->problem->events[eid].no_students();
        }
    }

    return total_cost;

}



size_t Solution::compute_daily_cost()
{

}

void Solution::reposition(map <int,Sol> &moves)
{
    for(auto &[event_id,sol_item]:moves)
    {
        this->memory[event_id]=this->schedule_set[event_id];
        this->unschedule(event_id);
        this->schedule(event_id,sol_item.room,sol_item.period);
    }
}

void Solution::rollback()
{
    for(auto &[event_id,sol_item]:this->memory)
    {
        this->unschedule(event_id);
        this->schedule(event_id,sol_item.room,sol_item.period);
    }
    this->memory.clear();
}

void Solution::schedule(const int &pevent,const int &room,const int &period)
{
    this->schedule_set[pevent]=Sol(period,room);
    this->periodwise_solutions[period].emplace_back(pevent);
    this->roomwise_solutions[room].emplace_back(pevent);
    // Calculate partial cost
}

void Solution::unschedule(const int &event)
{
    this->roomwise_solutions[this->schedule_set[event].room].erase(find(this->roomwise_solutions[this->schedule_set[event].room].begin(),this->roomwise_solutions[this->schedule_set[event].room].end(),event));
    this->periodwise_solutions[this->schedule_set[event].period].erase(find(this->periodwise_solutions[this->schedule_set[event].period].begin(),this->periodwise_solutions[this->schedule_set[event].period].end(),event));
    this->schedule_set[event]=Sol(-1,-1);
    // calculate partial cost
}

bool Solution::can_be_moved(const int &event_id,const int &period_id,const vector <int> &excluded={})
{
    vector <int> eneighbors=this->problem->G.neighbors(event_id);
    for(auto &neighbor_event_id:eneighbors)
    {
        if(find(excluded.begin(),excluded.end(),neighbor_event_id)!=excluded.end()) continue;
        if(this->schedule_set[neighbor_event_id].period==period_id)
        {
            return false;
        }
    }

    for(auto &precedence_event_id:this->problem->precedence_events[event_id])
    {
        if(find(excluded.begin(),excluded.end(),precedence_event_id)!=excluded.end()) continue;
        if(period_id>this->schedule_set[precedence_event_id].period)
        {
            return false;
        }
    }

    return true;
}

bool Solution::room_availability(const int &event_id,const int &period,const int &room,const vector <int> &excluded)
{
    for(const auto &event_id2:this->roomwise_solutions[room])
    {
        if(find(excluded.begin(),excluded.end(),event_id2)!=excluded.end()) continue;
        if(this->schedule_set[event_id2].period==period)
        {
            return false;
        }
    }
    return true;
}

int Solution::select_random_event()
{
    return this->random_event(eng);
}

bool Solution::room_selection(map <int,Sol> &moves)
{
    vector <pair <int,int>> captured;
    vector <int> moves_keys;
    int event_period;


    for(auto&[event_id,sol_item]:moves)
    {
        moves_keys.emplace_back(event_id);
    }

    for(auto &[event_id,sol_item]:moves)
    {
        event_period=sol_item.period;
        for(int rid=0;rid<this->problem->R;rid++)
        {
            if(find(this->problem->event_available_rooms[event_id].begin(),this->problem->event_available_rooms[event_id].end(),rid)==this->problem->event_available_rooms[event_id].end()) continue;
            if(find_if(captured.begin(),captured.end(),[&](pair <int,int> &pr) {return pr.first==event_period && pr.second==rid;})!=captured.end()) continue;
            if(this->room_availability(event_id,event_period,rid,moves_keys))
            {
                sol_item.room=rid;
                captured.emplace_back(make_pair(event_period,rid));
            }
        }
    }

    return accumulate(moves.begin(),moves.end(),0,[&](const pair <int,Sol> &pr) {return pr.second.room!=-1;})==moves.size();
}

map <int,Sol> Solution::transfer()
{
    map <int,Sol> moves;
    bool move_validance;

    int event_id=this->select_random_event();
    for(int period_id=0;period_id<this->problem->P;period_id++)
    {
        if(this->can_be_moved(event_id,period_id))
        {
            moves[event_id]=Sol(period_id,-1);
        }
    }

    move_validance=this->room_selection(moves);
    if(move_validance)
    {
        return moves;
    }
    return map <int,Sol>();
}

map <int,Sol> Solution::swap()
{
    map <int,Sol> moves;
    bool move_validance;

    int event_id=this->select_random_event();
    int event_id2=this->select_random_event();
    while(event_id==event_id2)
    {
        event_id2=this->select_random_event();
    }

    if(this->can_be_moved(event_id,this->schedule_set[event_id2].period,{event_id2}) && this->can_be_moved(event_id2,this->schedule_set[event_id].period,{event_id}))
    {
        moves[event_id]=Sol(this->schedule_set[event_id2].period,-1);
        moves[event_id2]=Sol(this->schedule_set[event_id].period,-1);
    }
    else
    {
        return map <int,Sol>();
    }
    if(this->room_selection(moves))
    {
        return moves;
    }
    return map <int,Sol>();
}

map <int,Sol> Solution::kempe_chain()
{
    stack <int> kc;
    int event_id1=this->select_random_event();
    
    vector <int> eneighbors=this->problem->G.neighbors(event_id1);
    uniform_int_distribution <int> neighbor_selector(0,eneighbors.size()-1);

    int event_id2=neighbor_selector(eng);

    map <int,int> versus_period={
        {this->schedule_set[event_id1].period,this->schedule_set[event_id2].period},
        {this->schedule_set[event_id2].period,this->schedule_set[event_id1].period}
    };

    map <int,Sol> moves;
    kc.push(event_id1);
    int current_event,new_period;


    while(!kc.empty())
    {
        current_event=kc.top();
        kc.pop();
        new_period=versus_period[this->schedule_set[current_event].period];
        moves[current_event]=Sol(new_period,-1);
        eneighbors=this->problem->G.neighbors(current_event);
        for(auto &neighbor_id:eneighbors)
        {
            if(moves.find(neighbor_id)!=moves.end()) continue;
            if(this->schedule_set[neighbor_id].period==new_period)
            {
                kc.push(neighbor_id);
            }
        }
    }

    if(this->room_selection(moves))
    {
        return moves;
    }

    return map<int,Sol>();
}

void Solution::build_double_kempe_chain(const int &event_id,map <int,Sol> &moves)
{
    vector <int> eneighbors=this->problem->G.neighbors(event_id);
    uniform_int_distribution <int> rand_neighbor(0,eneighbors.size()-1);
    int random_neighbor=eneighbors.at(rand_neighbor(eng));
    int count_failures=0;

    while(moves.find(random_neighbor)!=moves.end())
    {
        random_neighbor=eneighbors.at(rand_neighbor(eng));
        count_failures++;
        if(count_failures==eneighbors.size()) return;
    }

    stack <int> kc;
    map <int,int> versus_period={
        {moves[event_id].period,this->schedule_set[random_neighbor].period},
        {this->schedule_set[random_neighbor].period,moves[event_id].period}
    };

    int current_event,kempe_period,update_period;
    vector <int> eneighbors;
    kc.push(event_id);
    map <int,Sol> secondary_moves_map;

    while(!kc.empty())
    {
        current_event=kc.top();
        kc.pop();
        if(moves.find(current_event)!=moves.end())
        {
            update_period=moves[current_event].period;
        }
        else 
        {
            update_period=this->schedule_set[current_event].period;
        }
        kempe_period=versus_period[update_period];
        secondary_moves_map[current_event]=Sol(kempe_period,-1);
        eneighbors=this->problem->G.neighbors(current_event);
        for(auto &neighbor_id:eneighbors)
        {
            if(moves.find(neighbor_id)!=moves.end() || secondary_moves_map.find(neighbor_id)!=secondary_moves_map.end()) continue;
            if(this->schedule_set[neighbor_id].period==kempe_period)
            {
                kc.push(neighbor_id);
            }
        }
    }
    if(secondary_moves_map.size()>2)
    moves.insert(secondary_moves_map.begin(),secondary_moves_map.end());
}

map <int,Sol> Solution::double_kempe_chain()
{
    map <int,Sol> kempe_chain_level1=this->kempe_chain();
    map <int,Sol> kempe_chain_level1_copy=kempe_chain_level1;
    if(kempe_chain_level1.empty())
    {
        return map <int,Sol>();
    }

    for(const auto&[event_id,sol_item]:kempe_chain_level1_copy)
    {
        this->build_double_kempe_chain(event_id,kempe_chain_level1);
    }

    if(this->room_selection(kempe_chain_level1))
    {
        return kempe_chain_level1;
    }
    return map <int,Sol>();
}