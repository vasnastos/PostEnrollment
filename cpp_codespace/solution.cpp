#include "solution.h"

Sol::Sol(int p_,int r_):period(p_),room(r_) {}

Solution::Solution(string filename)
{
    this->problem=new Problem;
    this->problem->read(filename);
    this->mt=std::mt19937(std::random_device());
    this->rand_event.param(std::uniform_int_distribution<>::param_type(0,this->problem->E-1));
}

Solution::~Solution()
{
    delete this->problem;
}

int Solution::schedule(int &event_id,int &period_id,int &room_id)
{
    if(this->solution_set.find(event_id)==this->solution_set.end())
    {
        this->solution_set[event_id]=Sol(period_id,room_id);
    }

    this->periodwise_solutions[period_id].emplace_back(event_id);
    this->roomwise_solutions[room_id].emplace_back(event_id);
}

int Solution::unschedule(int &event_id)
{
    std::remove(this->periodwise_solutions[this->solution_set[event_id].period].begin(),this->periodwise_solutions[this->solution_set[event_id].period].end(),event_id);
    std::remove(this->roomwise_solutions[this->solution_set[event_id].room].begin(),this->roomwise_solutions[this->solution_set[event_id].room].end(),event_id);

    this->solution_set[event_id].period=-1;
    this->solution_set[event_id].room=-1;

}

int Solution::compute_cost()
{
    size_t cost=0;
    vector <int> student_periods;
    int no_of_daily_events,consecutive;
    for(int student_id=0;student_id<this->problem->S;student_id++)
    {
        student_periods.clear();

        for(auto &event_id:this->problem->students[student_id])
        {
            student_periods.emplace_back(this->solution_set[event_id].period);
        }

        for(int day=0;day<this->problem->number_of_days;day++)
        {
            no_of_daily_events=std::count_if(student_periods.begin(),student_periods.end(),[&](const int &period_id) {return period_id%this->problem->number_of_periods==day;});
            if(no_of_daily_events==1)
            {
                cost++;
            }
            else if(no_of_daily_events>=3)
            {
                consecutive=0;
                for(int period_id=day*this->problem->number_of_periods;period_id<day*this->problem->number_of_periods+this->problem->number_of_periods;period_id++)
                {
                    if(std::find(student_periods.begin(),student_periods.end(),period_id)!=student_periods.end())
                    {
                        consecutive++;
                    }
                    else
                    {
                        if(consecutive>2)
                        {
                            cost+=(consecutive-2);
                        }
                        consecutive=0;
                    }
                }
                if(consecutive>2)
                {
                    cost+=(consecutive-2);
                }
            }
        }
    }

    for(int event_id=0;event_id<this->problem->E;event_id++)
    {
         if(std::find(this->problem->final_periods_per_day.begin(),this->problem->final_periods_per_day.end(),this->solution_set[event_id].period)!=this->problem->final_periods_per_day.end())
         {
            cost+=this->problem->events[event_id].students.size();
         }
    }

    return cost;
}

int Solution::compute_daily_cost(int day)
{
    int daily_cost=0;
    int consecutive=0;
    vector <int> student_periods;
    for(int student_id=0;student_id<this->problem->S;student_id++)
    {
        student_periods.clear();
        for(auto &event_id:this->problem->students[student_id])
        {
            if(this->solution_set[event_id].period%this->problem->number_of_periods==day)
            {
                student_periods.emplace_back(this->solution_set[event_id].period);
            }

            if(std::find(this->problem->final_periods_per_day.begin(),this->problem->final_periods_per_day.end(),this->solution_set[event_id].period)!=this->problem->final_periods_per_day.end())
            {
                daily_cost++;
            }
        }

        if(student_periods.size()==1)
        {
            daily_cost++;
        }
        else if(student_periods.size()>=3)
        {
            consecutive=0;
            for(int period_id=day*this->problem->number_of_periods;period_id<day*this->problem->number_of_periods+this->problem->number_of_periods;period_id++)
            {
                if(std::find(student_periods.begin(),student_periods.end(),period_id)!=student_periods.end())
                {
                    consecutive++;
                }
                else
                {
                    if(consecutive>2)
                    {
                        daily_cost+=(consecutive-2);
                    }
                    consecutive=0;
                }
            }
            if(consecutive>2)
            {
                daily_cost+=(consecutive-2);
            }
        }
    }

}

map <int,Sol> Solution::transfer_event(int &event)
{
    
}

map <int,Sol> Solution::swap_events(int &event)
{

}

map <int,Sol> Solution::kempe_chain(int &event)
{

}

map <int,Sol> Solution::kick(int &event)
{

}

map <int,Sol> Solution::double_kick(int &event)
{

}

bool Solution::can_be_moved(const int &event,const int &period,const vector <int> &excluded={})
{

}

bool Solution::is_room_available(const int &room_id,const int &period_id)
{
    
}