#include "problem.h"

Problem::Problem() {}

void Problem::read(string filename)
{
    string line,word;
    vector <string> first_line_data;
    
    this->id=replaceString(filename,".tim","");
    fstream fp(filename,std::ios::in);

    // read first line
    getline(fp,line);
    stringstream ss(line);

    while(getline(ss,word,' '))
    {
        first_line_data.emplace_back(word);
    }

    this->E=stoi(first_line_data[0]);
    this->R=stoi(first_line_data[1]);
    this->F=stoi(first_line_data[2]);
    this->S=stoi(first_line_data[3]);

    this->events.resize(this->E);
    this->rooms.resize(this->R);

    // Start data reading
    for(int rid=0;rid<this->R;rid++)
    {
        getline(fp,line);
        this->rooms[rid].capacity=stoi(line);
    }

    // Event-Student relations
    for(int eid=0;eid<this->E;eid++)
    {
        for(int sid=0;sid<this->S;sid++)
        {
            getline(fp,line);
            if(stoi(line)==1)
            {
                this->events[eid].students.insert(sid);
            }
        }
    }

    // Room-Feature relations
    for(int rid=0;rid<this->R;rid++)
    {
        for(int fid=0;fid<this->F;fid++)
        {
            getline(fp,line);
            if(stoi(line)==1)
            {
                this->rooms[rid].features.insert(fid);
            }
        }
    }

    // Event feature relation
    for(int eid=0;eid<this->E;eid++)
    {
        for(int fid=0;fid<this->F;fid++)
        {
            getline(fp,line);
            if(stoi(line)==1)
            {
                this->events[eid].features.insert(fid);
            }
        }
    }

    // get formulation and if precedence relations are tracked continue to the following mods
    for(int eid=0;eid<this->E;eid++)
    {
        for(int pid=0;pid<this->P;pid++)
        {
            getline(fp,line);
            if(stoi(line)==1)
            {
                this->event_available_periods[eid].emplace_back(pid);
            }
        }
    }

    // Precedence relations between events
    for(int eid=0;eid<this->E;eid++)
    {
        for(int eid2=0;eid2<this->E;eid2++)
        {
            getline(fp,line);
            if(line=="") break;
            if(stoi(line)==1)
            {
                this->events[eid].precedence_events.emplace_back(eid2);
            }
            else if(stoi(line)==-1)
            {
                this->events[eid2].precedence_events.emplace_back(eid);
            }
        }
    }

    fp.close();

    // Create event-event relations based on common students
    set <int> common_students;
    
    for(int e1=0;e1<this->E;e1++)
    {
        this->G.add_node(e1);
        for(int e2=e1+1;e2<this->E;e2++)
        {
            std::set_intersection(this->events[e1].students.begin(),this->events[e1].students.end(),this->events[e2].students.begin(),this->events[e2].students.end(),common_students.begin());
            if(common_students.size()>0)
            {
                this->G.add_edge(e1,e2,common_students.size());
            }
            common_students.clear();
        }
    }

    // Create room-event availability relations
    for(int eid=0;eid<this->E;eid++)
    {
        for(int rid=0;rid<this->R;rid++)
        {
            if(std::includes(this->rooms[rid].features.begin(),this->rooms[rid].features.end(),this->events[eid].features.begin(),this->events[eid].features.end()))
            {
                this->event_available_rooms[eid].emplace_back(rid);
            }
        }
    }

    for(int day=0;day<this->number_of_days;day++)
    {
        this->final_periods_per_day.emplace_back(day*this->number_of_periods+this->number_of_periods-1);
    }
}

double Problem::density()
{
    return 2*this->G.number_of_edges()/this->G.number_of_nodes()*(this->G.number_of_nodes()-1);
}

double Problem::average_room_suitability()
{
    auto s=accumulate(this->event_available_rooms.begin(),this->event_available_rooms.end(),0,[&](int s,const pair <int,vector <int>> &pav) {return s+pav.second.size();});
    return static_cast<double>(s)/(this->R*this->E);
}

double Problem::average_room_size()
{
    return accumulate(this->rooms.begin(),this->rooms.end(),0,[&](int s,const Room &room) {return s+room.capacity;});
}

double Problem::precedence_density()
{
    
}

string Problem::get_id()const
{
    return this->id;
}
