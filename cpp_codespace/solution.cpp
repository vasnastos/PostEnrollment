#include "solution.h"

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


Problem* Solution::get_problem()
{
    return this->problem;
}

int Solution::schedule(const int &event_id,const int &room_id,const int &period_id)
{
    if(this->solution_set.find(event_id)==this->solution_set.end())
    {
        this->solution_set[event_id]=Sol(period_id,room_id);
    }

    this->periodwise_solutions[period_id].emplace_back(event_id);
    this->roomwise_solutions[room_id].emplace_back(event_id);
}

int Solution::unschedule(const int &event_id)
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
    return daily_cost;
}

void Solution::set_tournment_size(const int &size)
{
    this->tournment_size=size;
}

int Solution::get_tournament_size()const
{
    return this->tournment_size;
}

int Solution::tournament_selection()
{
    // Adapt tournment selectionat moves selection
    // 1. We can tryu tournment selection based on the move ratio show
    // 2. Or based on the neighbors score
}


map <int,Sol> Solution::transfer_event(const int &event)
{

    for(int period_id=0;period_id<this->problem->P;period_id++)
    {
        if(period_id==this->solution_set[event].period) continue;
        if(this->can_be_moved(event,period_id))
        {
            for(int room_id=0;room_id<this->problem->R;room_id++)
            {
                if(this->is_room_available(event,room_id,period_id))
                {
                    return {
                        {event,Sol(period_id,room_id)}
                    };
                }
            }
        }
    }
    return map <int,Sol>();
}

map <int,Sol> Solution::swap_events(const int &event)
{
    vector <int> eneighbors=this->problem->G.neighbors(event);
    for(auto &event_id2:eneighbors)
    {
        if(this->can_be_moved(event,this->solution_set[event_id2].period,{event_id2}) && this->can_be_moved(event_id2,this->solution_set[event].period,{event}))
        {
            // Keep the same room
            if(this->is_room_available(event,this->solution_set[event].room,this->solution_set[event_id2].period) && this->is_room_available(event_id2,this->solution_set[event].room,this->solution_set[event_id2].period))
            {
                return {
                    {event,Sol(this->solution_set[event_id2].period,this->solution_set[event].room)},
                    {event_id2,Sol(this->solution_set[event].period,this->solution_set[event_id2].room)}
                };
            }
            else if(this->is_room_available(event,this->solution_set[event_id2].room,this->solution_set[event_id2].period,{event_id2}) && this->is_room_available(event_id2,this->solution_set[event].room,this->solution_set[event].period,{event}))
            {
                return {
                    {event,Sol(this->solution_set[event_id2])},
                    {event_id2,Sol(this->solution_set[event])}
                };
            }
            else
            {
                map <int,Sol> moves={
                    {event,Sol(this->solution_set[event_id2].period,-1)},
                    {event_id2,Sol(this->solution_set[event].period,-1)}
                };

                // Find suitable room for the first event
                for(int room_id=0;room_id<this->problem->R;room_id++)
                {
                    if(room_id==this->solution_set[event].room || room_id==this->solution_set[event_id2].room) continue;
                    if(this->is_room_available(event,room_id,moves[event].period))
                    {
                        moves[event].room=room_id;
                        break;
                    }
                }

                // Find suitable room for the second event
                for(int room_id=0;room_id<this->problem->R;room_id++)
                {
                    if(room_id==this->solution_set[event].room || room_id==this->solution_set[event_id2].room) continue;
                    if(this->is_room_available(event_id2,room_id,moves[event_id2].period))
                    {
                        moves[event_id2].room=room_id;
                        break;
                    }
                }

                if(moves[event].room!=-1 && moves[event_id2].room!=-1)
                {
                    return moves;
                }
            }
        }   
    }
    return map <int,Sol>();
}

map <int,Sol> Solution::kempe_chain(const int &event)
{
    map <int,Sol> moves;
    queue <int> kc;
    vector <int> eneighbors=this->problem->G.neighbors(event);
    vector <int> eneighbors2;
    map <int,int> versus_periods;
    map <int,int> connections;
    bool valid_move,stop_flag,first_connection;
    int current_event;
    int next_period;
    for(auto &event_id2:eneighbors)
    {
        valid_move=(find(this->problem->event_available_periods[event].begin(),this->problem->event_available_periods[event].end(),this->solution_set[event_id2].period)!=this->problem->event_available_periods[event].end()) && (find(this->problem->event_available_periods[event_id2].begin(),this->problem->event_available_periods[event_id2].end(),this->solution_set[event].period)!=this->problem->event_available_periods[event_id2].end());
        if(!valid_move) continue;
        
        kc=queue<int>();
        connections.clear();
        moves.clear();

        versus_periods={
            {this->solution_set[event].period,this->solution_set[event_id2].period},
            {this->solution_set[event_id2].period,this->solution_set[event].period}
        };

        kc.push(event);
        stop_flag=false;
        while(!kc.empty())
        {
            current_event=kc.front();
            kc.pop();
            next_period=versus_periods[this->solution_set[current_event].period];
            valid_move=(find(this->problem->event_available_periods[current_event].begin(),this->problem->event_available_periods[current_event].end(),next_period)!=this->problem->event_available_periods[current_event].end());
            if(!valid_move)
            {
                stop_flag=true;
                break;
            }
            moves[current_event]=Sol(next_period,-1);
            eneighbors2=this->problem->G.neighbors(current_event);
            first_connection=true;
            for(auto &event_id2:eneighbors2)
            {
                if(moves.find(event_id2)!=moves.end())
                {
                    continue;
                }
                if(first_connection)
                {
                    first_connection=false;
                    connections[current_event]=event_id2;
                }
                kc.push(event_id2);
            }
        }
        if(stop_flag) continue;
        for(auto &[event_id,sol_item]:moves)
        {
            // 1. Try to put the event in the same room
            if(this->is_room_available(event_id,this->solution_set[event_id].room,sol_item.period))
            {
                sol_item.room=this->solution_set[event_id].room;
            }

            // 2. Try to place the event in its connection room
            else if(this->is_room_available(event_id,this->solution_set[connections[event_id]].room,sol_item.period,{connections[event_id]}))
            {
                sol_item.room=this->solution_set[connections[event_id]].room;
            }

            else
            {
                for(int room_id=0;room_id<this->problem->R;room_id++)
                {
                    if(room_id==this->solution_set[event_id].room || room_id==this->solution_set[connections[event_id]].room)
                    {
                        continue;
                    }
                    if(this->is_room_available(event_id,room_id,sol_item.period))
                    {
                        sol_item.room=room_id;
                    }
                }
            }

            if(sol_item.room==-1)
            {
                return map <int,Sol>();
            }
        }
        return moves;
    }
    return map <int,Sol>();
}

map <int,Sol> Solution::kick(const int &event)
{
    auto eneighbors=this->problem->G.neighbors(event);
    for(auto &event_id2:eneighbors)
    {
        if(this->can_be_moved(event,this->solution_set[event_id2].period,{event_id2}))
        {
            for(int period_id=0;period_id<this->problem->P;period_id++)
            {
                if(this->can_be_moved(event_id2,period_id))
                {
                    map <int,Sol> potential_moves={
                        {event,Sol(this->solution_set[event_id2].period,-1)},
                        {event_id2,Sol(period_id,-1)}
                    };
                    // Find suitable room for event 1
                    for(int room_id=0;room_id<this->problem->R;room_id++)
                    {
                        if(this->is_room_available(event,room_id,potential_moves[event].period,{event_id2}))
                        {
                            potential_moves[event].room=room_id;
                            break;
                        }
                    }

                    if(potential_moves[event].room!=-1)
                    {
                        for(int room_id=0;room_id<this->problem->R;room_id++)
                        {
                            if(this->is_room_available(event_id2,room_id,potential_moves[event_id2].period))
                            {
                                potential_moves[event_id2].room=room_id;
                                break;
                            }
                        }
                    }

                    if(potential_moves[event].room!=-1 && potential_moves[event_id2].room!=-1)
                    {
                        return potential_moves;
                    }
                }
            }
        }
    }
    return map <int,Sol>();
}

map <int,Sol> Solution::double_kick(const int &event)
{
    vector <int> eneighbors,eneighbors2;
    map <int,Sol> moves;
    eneighbors=this->problem->G.neighbors(event);
    for(auto &event_id2:eneighbors)
    {
        if(this->can_be_moved(event,this->solution_set[event_id2].period,{event_id2}))
        {
            eneighbors2=this->problem->G.neighbors(event_id2);
        
            for(auto &event_id3:eneighbors2)
            {
                if(event_id3==event) continue;
                if(this->can_be_moved(event_id2,this->solution_set[event_id3].period,{event_id3}))
                {
                    for(int period_id=0;period_id<this->problem->P;period_id++)
                    {
                        if(this->can_be_moved(event_id2,period_id,{event}))
                        {
                            moves={
                                {event,Sol(this->solution_set[event_id2].period,-1)},
                                {event_id2,Sol(this->solution_set[event_id3].period,-1)},
                                {event_id3,Sol(period_id,-1)}
                            };

                            // 1. Place the first event
                            if(this->is_room_available(event,this->solution_set[event].room,moves[event].period))
                            {
                                moves[event].room=this->solution_set[event].room;
                            }
                            else if(this->is_room_available(event,this->solution_set[event_id2].room,moves[event].period,{event_id2}))
                            {
                                moves[event].room=this->solution_set[event_id2].room;
                            }
                            else{
                                for(int room_id=0;room_id<this->problem->R;room_id++)
                                {
                                    if(room_id==this->solution_set[event].room || room_id==this->solution_set[event_id2].room) continue;
                                    if(this->is_room_available(event,room_id,moves[event].period))
                                    {
                                        moves[event].room=room_id;
                                        break;
                                    }
                                }
                            }

                            if(moves[event].room==-1) continue;

                            // 2. Place the second event
                            if(this->is_room_available(event_id2,this->solution_set[event_id2].room,moves[event_id2].period))
                            {
                                moves[event_id2].room=this->solution_set[event_id2].room;
                            }
                            else if(this->is_room_available(event_id2,this->solution_set[event_id3].room,moves[event_id3].period,{event_id3}))
                            {
                                moves[event_id2].room=this->solution_set[event_id3].room;
                            }
                            else
                            {
                                for(int room_id=0;room_id<this->problem->R;room_id++)
                                {
                                    if(room_id==this->solution_set[event_id2].room || room_id==this->solution_set[event_id3].room) continue;
                                    if(this->is_room_available(event,room_id,moves[event].period))
                                    {
                                        moves[event_id2].room=room_id;
                                        break;
                                    }
                                }
                            }

                            if(moves[event_id2].room==-1) continue;

                            // 3. Place the third event
                            for(int room_id=0;room_id<this->problem->R;room_id++)
                            {
                                if(this->is_room_available(event_id3,room_id,moves[event_id3].period,{event,event_id2}))
                                {
                                    moves[event_id3].period=room_id;
                                    break;
                                }
                            }

                            if(moves[event_id3].room==-1) continue;

                            return moves;
                        }
                    }
                }
            }
        }
    }
    return map <int,Sol>();
}

bool Solution::can_be_moved(const int &event,const int &period,const vector <int> &excluded={})
{
    vector <int> eneighbors=this->problem->G.neighbors(event);
    for(auto &event_id2:eneighbors)
    {
        if(find(excluded.begin(),excluded.end(),event_id2)!=excluded.end()) continue;
        if(this->solution_set[event_id2].period==period)
        {
            return false;
        }
    }
    return true;
}

bool Solution::is_room_available(const int &event_id,const int &room_id,const int &period_id,const vector <int> &excluded={})
{
    if(find(this->problem->event_available_periods[event_id].begin(),this->problem->event_available_periods[event_id].end(),period_id)==this->problem->event_available_periods[event_id].end()) return false;
    for(auto &event_id2:this->periodwise_solutions[period_id])
    {
        if(find(excluded.begin(),excluded.end(),event_id2)!=excluded.end()) continue;
        if(this->solution_set[event_id2].room==room_id)
        {
            return false;
        }
    }
    return true;
}

void Solution::reposition(const int &event,const int &room,const int &period_id)
{
    this->memory[event]=Sol(period_id,room);
    this->unschedule(event);
    this->schedule(event,room,period_id);
}

void Solution::reposition(map <int,Sol> &moves)
{
    for(auto &[event_id,sol_item]:moves)
    {
       this->reposition(event_id,sol_item.room,sol_item.period);
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

void Solution::set_solution(map <int,Sol> &candicate_solution)
{
    for(auto &[event_id,sol_item]:candicate_solution)
    {
        this->unschedule(event_id);
        this->schedule(event_id,sol_item.room,sol_item.period);
    }
}

map <int,Sol> Solution::select_operator(string &move_name)
{
    uniform_int_distribution <int> movernd(1,5);
    int randmove=movernd(mt);
    int event=this->rand_event(mt);

    if(randmove==1)
    {
        move_name="Transfer";
        return this->transfer_event(event);
    }
    else if(randmove==2)
    {
        move_name="Swap";
        return this->swap_events(event);
    }
    else if(randmove==3)
    {
        move_name="Kempe";
        return this->kempe_chain(event);
    }
    else if(randmove==4)
    {
        move_name="Kick";
        return this->kick(event);
    }
    else
    {
        move_name="Double Kick";
        return this->double_kick(event);
    }
}

void Solution::save()
{
    fs::path filepath(".");
    vector <string> path_road={"..","results",this->problem->get_id()+"_"+std::to_string(this->compute_cost())};
    for(const string &x:path_road)
    {
        filepath.append(x);
    }


    fstream fp(filepath.string(),ios::out);
    for(auto &[event_id,sol_item]:this->solution_set)
    {
        fp<<sol_item.period<<" "<<sol_item.room<<endl;
    }
    fp.close();
}