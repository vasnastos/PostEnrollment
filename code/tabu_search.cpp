#include "tabu_search.hpp"


TSSP::TSSP(Solution *sol_item,size_t solution_time):solution(sol_item),elapsed_time(solution_time)
{
    for(int event_id=0,t=this->solution->get_problem()->E;event_id<t;event_id++)
    {
        this->unassigned_events.emplace_back(event_id);
        this->best_solution[event_id]=Sol(-1,-1);
    }

}

bool TSSP::tssp_elapsed()
{
    auto end_timer=high_resolution_clock::now();
    return duration_cast<seconds>(end_timer-this->start_timer).count()>this->elapsed_time;
}

double TSSP::objective_function(vector <int> &unplaced_events)
{
    double obj_value=0.0;
    for(auto &event_id:unplaced_events)
    {
        obj_value+=1.0+(static_cast<double>(this->solution->get_problem()->clash(event_id))/this->solution->get_problem()->sum_clash());
    }
    return obj_value;
}

vector <int> TSSP::sampling(vector <int> &unplaced_events)
{
    vector <int> sample_events;
    uniform_int_distribution <int> rr(0,unplaced_events.size()-1);
    for(int i=0,ts=0.0025*this->solution->get_problem()->E;i<ts;i++)
    {
        sample_events.emplace_back(rr(this->solution->eng));
    }
    return sample_events;
}

vector <int> TSSP::conflicting_events(const int &event_id,const int &period_id)
{
    vector <int> confe;
    vector <int> eneighbors=this->solution->get_problem()->G.neighbors(event_id);
    for(auto &event_id2:eneighbors)
    {
        if(event_id==event_id2 || this->current_solution[event_id2].period==-1) continue;
        if(this->current_solution[event_id2].period==period_id)
        {
            confe.emplace_back(event_id2);
        }
    }
    return confe;

}

bool TSSP::define_tabu(vector <int> &confe)
{
    map <int,int> tabu_solution;
    for(auto &conflicting_event_id:confe)
    {
        tabu_solution[conflicting_event_id]=this->current_solution[conflicting_event_id].period;
    }
    if(find(this->tabulist.begin(),this->tabulist.end(),tabu_solution)!=this->tabulist.end())
    {
        return true;
    }

    this->tabulist.emplace_back(tabu_solution);
    return false;
}

void TSSP::solve()
{
    vector <int> unplaced=this->unassigned_events;
    this->current_solution=this->best_solution;
    this->best_cost=INT16_MAX;
    int min_search_cost;

    vector <int> sample_events;
    vector <int> eneighbors;
    vector <int> confe;
    map <int,Sol> memory;
    int fobj,best_event=-1,best_slot=-1;
    int iter_id=1;
    bool check_flag;
    size_t NUM_ITERS=pow(this->solution->get_problem()->R,3);
    
    
    start_timer=high_resolution_clock::now();
    while(!unplaced.empty() && !this->tssp_elapsed())
    {
        min_search_cost=INT16_MAX;
        best_event=-1;
        best_slot=-1;
        sample_events=this->sampling(unplaced);

        for(auto &event_id:sample_events)
        {
            unplaced.erase(find(unplaced.begin(),unplaced.end(),event_id));
            for(int period_id,NP=this->solution->get_problem()->P;period_id<NP;period_id++)
            {
                memory.clear();
                if(find(this->solution->get_problem()->event_available_periods[event_id].begin(),this->solution->get_problem()->event_available_periods[event_id].end(),period_id)==this->solution->get_problem()->event_available_periods[event_id].end()) continue;
                
                check_flag=true;
                if(DatasetDB::get_instance()->has_precedence_relation(this->solution->get_problem()->get_id()))
                {
                    for(auto &event_id2:this->solution->get_problem()->precedence_events[event_id])
                    {
                        if(find(unplaced.begin(),unplaced.end(),event_id2)!=unplaced.end())
                        {
                            continue;
                        }
                        if(period_id>this->current_solution[event_id2].period)
                        {
                            check_flag=false;
                            break;
                        }
                    }
                }

                if(!check_flag) continue;

                // find conflicting events for event_id
                confe=this->conflicting_events(event_id,period_id);
                for(auto &conflicting_event_id:confe)
                {
                    memory[conflicting_event_id]=this->current_solution[conflicting_event_id];
                    this->current_solution.erase(conflicting_event_id);
                    unplaced.emplace_back(conflicting_event_id);
                }

                fobj=this->objective_function(unplaced);
                if(fobj<min_search_cost)
                {
                    best_event=event_id;
                    best_slot=period_id;
                    min_search_cost=fobj;
                }

                for(auto &conflicting_event_id:confe)
                {
                    unplaced.erase(find(unplaced.begin(),unplaced.end(),conflicting_event_id));
                    this->current_solution[conflicting_event_id]=memory[conflicting_event_id];
                }
            }
            unplaced.emplace_back(event_id);
        }

        if(best_event==-1) continue;

        confe=this->conflicting_events(best_event,best_slot);
        if(this->define_tabu(confe)) continue;  // if the solution is a tabu one continue the execution

        // Remove event from current solution and replace the best cost with the min_search_cost if min_search_cost<best_cost
        for(auto &event_id:confe)
        {
            this->current_solution.erase(event_id);
        }
        this->current_solution[best_event]=Sol(best_slot,-1);
        fobj=min_search_cost;
        if(fobj<this->best_cost)
        {
            this->best_solution=this->current_solution;
            this->best_cost=fobj;
            this->unassigned_events=unplaced;
            cout<<"TSSP| Iter:"<<iter_id<<"\tEvent Select:"<<best_event<<"\tSlot Selected:"<<best_slot<<"\tObj:"<<fobj<<endl;
        }

        // Remove from the unplaced set the best event and add to the unplaced set the conflicting events 
        unplaced.erase(find(unplaced.begin(),unplaced.end(),best_event));
        for(auto &event_id:confe)
        {
            unplaced.emplace_back(event_id);
        }


        // Room insertion - PERTURB the current solution
        if(iter_id==NUM_ITERS)
        {
            // PERTURB the solution in search of rooms
            iter_id=0;
            this->tabulist.clear();
        }
        iter_id++;
    }
}

map <int,Sol> TSSP::get_best_solution()
{
    return this->best_solution;
}




// Pseudocode

// procedure TS(best, unassignedE)
//     unplacedE ← unassignedE
//     current ← best
//     f (best ) ← f (current )
//     while unplacedE is not empty AND time.elapsed () < T do
//         min ← ∞
//         for all e ∈ unplacedE do
//             unplacedE ← unplacedE − e
//             for all s ∈ S | S non-tabu slot suitable for e do
//             current ← current − {events conﬂicting e}
//             unplacedE ← unplacedE ∪ {events conﬂicting e}
//             if f (candidate ) < min then
//                 bestE vent ← e
//                 bestSlot ← s
//                 min ← f (candidate )    
//             end if
//             unplacedE ← unplacedE − {events conﬂicting e}
//             current ← current ∪ {events conﬂicting e}
//         end for
//         unplacedE ← unplacedE ∪ e
//         end for
//         current ← current − {events conﬂicting bestEvent}
//         current ← current ∪ bestE vent ->bestSlot
//         f (current ) ← min
//         if f (current ) < f (best ) then
//             best ← current
//             f (best ) ← f (current )
//             unassignedE ← unplacedE
//             end if
//         set tabu {events conﬂicting bestEvent} from original time slots
//         unplacedE ← unplacedE − bestE vent
//         unplacedE ← unplacedE ∪ {events conﬂicting bestEvent}
//         end while
// end procedure