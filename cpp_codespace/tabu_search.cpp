#include "tabu_search.h"

TabuInit::TabuInit(Problem *p):problem(p) {
    this->clashsum=0;
    for(int eid=0;eid<this->problem->E;eid++)
    {
        this->clashsum+=this->problem->clashe(eid);
    }

}

void TabuInit::create_unassigned() 
{
    this->unplaced.clear();
    for(int eid=0;eid<this->problem->E;eid++)
    {
        this->unplaced.emplace_back(eid);
    }
}


int TabuInit::objective()
{
    return accumulate(this->unplaced.begin(),this->unplaced.end(),0.0,[&](double s,const int &event_id) {return s+(1+(this->problem->clashe(event_id)/this->clashsum));});
}

void TabuInit::find_conflicting_events(int &event_id,int &period_id)
{
    this->conflicted_events.clear();
    for(auto &cevent:this->problem->G.neighbors(event_id))
    {
        if(this->period_solution.find(cevent)!=this->period_solution.end())
        {
            if(this->period_solution[cevent]==period_id)
            {
                this->conflicted_events.emplace_back(cevent);
            }
        }
    }
}

void TabuInit::remove(int &event_id)
{
    for(auto &event_id2:this->conflicted_events)
    {
        if(this->period_solution.find(event_id2)!=this->period_solution.end())
        {
            this->memory[event_id2]=this->period_solution[event_id2];
            this->period_solution.erase(event_id2);
        }

        if(find(this->unplaced.begin(),this->unplaced.end(),event_id2)==this->unplaced.end())
        {
            this->unplaced.emplace_back(event_id2);
        }
    }
}

void TabuInit::rollback(int &event_id)
{
    for(auto &event_id2:this->conflicted_events)
    {
        auto sitr=find(this->unplaced.begin(),this->unplaced.end(),event_id2);
        if(sitr!=this->unplaced.end())
        {
            this->unplaced.erase(sitr);
        }
    }

    for(auto &[event_id,period_id]:this->memory)
    {
        this->period_solution[event_id]=period_id;
    }

    this->memory.clear();

}

bool TabuInit::tabu(const int &event_id)
{
    // Add candicate solution(conflicted events only) to tabu_list
    if(this->memory.size()!=0)
    {   
       if(find(this->tabu_list.begin(),this->tabu_list.end(),this->memory)!=this->tabu_list.end())
       {
         return true;
       }
       tabu_list.emplace_back(this->memory);
    }
    return false;
}

void TabuInit::perturb()
{
    
}

void TabuInit::tssp(int timesol) 
{
    auto best=this->period_solution;
    auto best_score=this->objective();
    size_t ITER=static_cast<int>(pow(this->problem->R,3));
    size_t i=0;
    int cnt_sample=0.0025*this->problem->E;
    int event_id;
    vector <int> sampleE;
    size_t min,solution_id=1;
    mt19937 mt(random_device());
    uniform_int_distribution <int> rand_event(0,this->unplaced.size()-1);
    vector <map <int,int>> tabu_list;
    bool is_tabu;

    auto start_timer=high_resolution_clock::now(); 

    int best_event;
    int best_period;

    while(!this->unplaced.empty() && duration_cast<seconds>(high_resolution_clock::now()-start_timer).count()<timesol)
    {
        sampleE.clear();
        min=INT_MAX;
        best_event=-1;
        best_period=-1;

        // 1. create sampleE set
        if(this->unplaced.size()<=cnt_sample)
        {
            for(auto &event_id:this->unplaced)
            {
                sampleE.emplace_back(event_id);
            }   
        }
        else{
            for(int j=0;j<cnt_sample;j++)
            {
                event_id=this->unplaced.at(rand_event(mt));
                while(find(sampleE.begin(),sampleE.end(),event_id)!=sampleE.end())
                {
                    event_id=this->unplaced.at(rand_event(mt));
                }
                sampleE.emplace_back(event_id);
            }
        }

        for(auto &event_id2:sampleE)
        {
            this->unplaced.erase(find(this->unplaced.begin(),this->unplaced.end(),event_id2));
            for(auto &period_id:this->problem->event_available_periods[event_id2])
            {
                this->find_conflicting_events(event_id2,period_id);           
                this->remove(event_id2);
                if(this->objective()<min)
                {
                    best_event=event_id2;
                    best_period=period_id;
                    min=this->objective();
                }
                this->rollback(event_id2);
            }
            this->unplaced.emplace_back(event_id2);
        }

        if(best_event!=-1)
        {   
            this->find_conflicting_events(best_event,best_period);
            this->remove(best_event);
            is_tabu=this->tabu(best_event);
            if(is_tabu)
            {
                this->rollback(best_event);
                continue;
            }
            this->period_solution[best_event]=best_period;

            // Place best event at the solution
            if(min<best_score)
            {
                best=this->period_solution;
                best_score=min;    
                cout<<"TS-Solution Updater|  Solution:"<<solution_id++<<"\tObjective:"<<best_score<<"\tUnplaced Score:"<<this->unplaced.size()<<"\tNumber of placed Events:"<<best.size()<<"\tTabu Solutions:"<<tabu_list.size()<<endl;        
            }

            // if the move executed is tested memory is cleared
            this->memory.clear();
        }

        // PERTURB ITER
        if(i==ITER)
        {
            i=0;
            this->perturb();
            tabu_list.clear();
        }
        if(i%(this->problem->R*2)==0) // Possible hyperparemeter
        {
            BipGraph bg(this->problem,this->period_solution);
            cout<<"Maximum number of events placed in rooms:"<<bg.hocroft_karp()<<endl;
            this->set_room_solution(bg.get_solution());
        }
        i++;
    }
}


void TabuInit::set_room_solution(map <int,int> &rsol)
{
    vector <int> unset;
    for(auto &[event_id,period]:this->period_solution)
    {
        if(rsol.find(event_id)!=rsol.end())
        {
            this->room_solution[event_id]=rsol[event_id];
        }
        else
        {
            unset.emplace_back(event_id);
        }
    }

    for(auto &event_id:unset)
    {
        this->period_solution.erase(this->period_solution.find(event_id));
        this->unplaced.emplace_back(event_id);
    }
}