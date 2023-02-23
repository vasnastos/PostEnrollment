#include "solution.hpp"

mt19937 rnde(high_resolution_clock::now().time_since_epoch().count());

Solution::Solution(Problem *p):problem(p),cost(0) {
    random_event.param(std::uniform_int_distribution<int>::param_type(0, this->problem->E-1));
}

Solution::~Solution() {}


// Operators
map <int,pair <int,int>> Solution::transfer_event()
{
    map <int,pair <int,int>> potential_solutions;
    auto event_id=random_event(rnde);
    for(int period=0;period<this->problem->P;period++)
    {
        if(this->can_be_moved(event_id,period,{}) && this->room_availability(event_id,this->solution_set[event_id].room))
        {
            potential_solutions[event_id]=make_pair(period,this->solution_set[event_id].room);
        }
    }
}

map <int,pair <int,int>> Solution::swap_events()
{
    map <int,pair <int,int>> potential_solutions;
    auto event1=this->random_event(rnde);
    int event2;
    bool partial_solution=false;
    auto neighbors=this->problem->G.neighbors(event1);
    while(neighbors.size()==0)
    {
        event1=this->random_event(rnde);
        neighbors=this->problem->G.neighbors(event1);
    }

    for(int i=0,t=neighbors.size();i<t;i++)
    {
        partial_solution=false;
        event2=neighbors[i].first;
        if(this->can_be_moved(event1,this->solution_set[event2].period,{event2}) && this->can_be_moved(event2,this->solution_set[event1].period,{event1}))
        {
            if(this->room_availability(this->solution_set[event2].period,this->solution_set[event1].room,{event2}))
            {    
                potential_solutions[event1]=make_pair(this->solution_set[event2].period,this->solution_set[event1].room);
                partial_solution=true;
            }
            else{
                for(int room_id=0;room_id<this->problem->R;room_id++)
                {
                    if(room_id==this->solution_set[event1].room) continue;
                    if(this->room_availability(this->solution_set[event2].period,room_id,{event2}))
                    {
                        potential_solutions[event1]=make_pair(this->solution_set[event2].period,room_id);
                        partial_solution=true;
                        break;
                    }
                }
            }

            if(!partial_solution)
            {
                continue;
            }

            if(this->room_availability(event2,this->solution_set[event2].room,{event1}))
            {
                potential_solutions[event2]=make_pair(this->solution_set[event1].period,this->solution_set[event2].room);
                partial_solution=false;
            }
            else 
            {
                for(auto room_id=0;room_id<this->problem->R;room_id++)
                {
                    if(room_id==this->solution_set[event2].room) continue;
                    if(this->room_availability(event2,room_id,{event1}))
                    {
                        potential_solutions[event2]=make_pair(this->solution_set[event1].period,room_id);
                        partial_solution=false;
                        break;
                    }
                }
            }

            if(!partial_solution)
            {
                //  if an acceptable solution is found then stop the search for an event that satisfies the opperator rules
                break;
            }
            else
            {
                potential_solutions.clear();
            }
        }
    }
}

map <int,pair <int,int>> Solution::kempe_chain()
{
    map <int,pair <int,int>> potential_solutions;
    map <int,int> versus_periods;
    map <int,int> moves;
    uniform_real_distribution <double> rand_real(0,100);
    auto event1=random_event(rnde);
    
    auto eneighbors=this->problem->G.neighbors(event1);
    double choose_based_on_day=rand_real(rnde);

    int current_event,period1,period2,new_period;

    for(auto &[event2,weight]:eneighbors)
    {
        versus_periods.clear();
        queue <int> kc;
        if(choose_based_on_day<60)
        {
            if(this->solution_set[event1].period%PEperiods==this->solution_set[event2].period%PEperiods)
            {
                continue;
            }
        }
        period1=this->solution_set[event1].period;
        period2=this->solution_set[event2].period;


        versus_periods={
            {period1,period2},
            {period2,period1}
        };


        // Track kempe chain with periodwise
        kc.push(event1);
        while(!kc.empty())
        {
            current_event=kc.front();
            kc.pop();
            auto ce_neighbors=this->problem->G.neighbors(current_event);
            new_period=versus_periods[current_event];
            moves[current_event]=new_period;
            for(auto &[neighbor_id,weight]:eneighbors)
            {
                if(this->solution_set[neighbor_id].period==new_period)
                {
                    kc.push(neighbor_id);
                }
            }
        }

        vector <int> excluded_events;
        transform(moves.begin(),moves.end(),excluded_events.begin(),[](const pair <int,int> &p) {return p.first;});

        // Find a suitable room
        for(auto &[event_id,period_id]:moves)
        {
            for(int rid=0;rid<this->problem->R;rid++)
            {
                if(this->room_availability(rid,moves[event_id],excluded_events))
                {
                    potential_solutions[event_id]=make_pair(moves[event_id],rid);
                }
            }

            if(potential_solutions.find(event_id)==potential_solutions.end()) break;
        }
    }
    return potential_solutions;
}


map <int,pair <int,int>> Solution::regroup()
{
    uniform_int_distribution <int> random_period(0,this->problem->P);
    auto new_timeslot=random_period(rnde);


    // Identify similar events possibly KMeans
    
}

map <int,pair <int,int>> Solution::perturbation()
{

}

// Cost calculation
int Solution::compute_cost()
{

}

int Solution::compute_partial_cost()
{

}

void Solution::customize_solution(map <int,pair <int,int>> &new_solution_set)
{
    this->solution_set.clear();
    for(auto &[event_id,sol]:new_solution_set)
    {
        this->solution_set[event_id]=ERSol(sol.first,sol.second);
        this->periodwise_solution[sol.first].emplace_back(event_id);
        this->roomwise_solution[sol.second].emplace_back(event_id);
    }
}