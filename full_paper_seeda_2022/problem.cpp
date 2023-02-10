#include "problem.hpp"

// Available categories
// 1. ConsDS
// 2. NoN-ConsDS

Event::Event(int exam_index):id(exam_index) {}

void Event::add_student(int sid)
{
    this->students.emplace_back(sid);
}

void Event::add_feature(int fid)
{
    this->features.insert(fid);
}


bool Event::operator==(const int candicate_id)
{
    return this->id==candicate_id;
}

string Event::to_string()const
{
    string message="Id:"+std::to_string(this->id)+"  [";
    for(auto &sid:this->students)
    {
        message+=std::to_string(sid)+" ";
    }
    message+="]";
    return message;
}


Room::Room(int room_id):id(room_id) {}

Room::Room(int room_id,int room_capacity):id(room_id),capacity(room_capacity) {}

Room::~Room() {}

void Room::add_feature(int feature_id) {this->features.insert(feature_id);}

bool Room::operator==(const int candicate_id)
{
    return this->id==candicate_id;
}

string Room::to_string()const
{
    string message="";
    message="Id:"+std::to_string(this->id)+" Features:[";
    for(auto &fid:this->features)
    {
        message+=std::to_string(fid)+" ";
    }
    message+="]";
    return message;
}

Problem::Problem(string filename,string formulationN):P(45)
{
    this->formulation=formulationN;
    string line,word;
    bool startline=true;

    fstream fp;
    fp.open(filename);
    getline(fp,line);
    {
        vector <string> linedata;
        
        stringstream ss(line);
        while(getline(ss,word,' '))
        {
            linedata.emplace_back(word);
        }

        assert(linedata.size()==4);
        this->E=stoi(linedata[0]);
        this->R=stoi(linedata[1]);
        this->F=stoi(linedata[2]);
        this->S=stoi(linedata[3]);
    }


    // Event configuration
    for(int eid=0;eid<this->E;eid++)
    {
        this->events.emplace_back(Event(eid));
    }

    // Room configuration
    for(int i=0;i<this->R;i++)
    {
        getline(fp,line);
        this->rooms.emplace_back(Room(i,stoi(line)));
    }
    //  Students per event
    for(int sid=0;sid<this->S;sid++)
    {
        for(int eid=0;eid<this->E;eid++)
        {
            getline(fp,line);
            if(stoi(line)==1)
            {
                this->events[eid].add_student(sid);
                this->students[sid].emplace_back(eid);
            }
        }
    }

    // Features per room
    for(int rid=0;rid<this->R;rid++)
    {
        for(int fid=0;fid<this->F;fid++)
        {
            getline(fp,line);
            if(stoi(line)==1)
            {
                this->rooms[rid].add_feature(fid);
            }
        }
    }

    // Features per event
    for(int eid=0;eid<this->E;eid++)
    {
        for(int fid=0;fid<this->F;fid++)
        {
            getline(fp,line);
            if(stoi(line)==1)
            {
                this->events[eid].add_feature(fid);
            }
        }
    }

    // Check the suitable formulation
    
    if(this->formulation=="ConsDS")
    {
        // Period suitability per event
        for(int eid=0;eid<this->E;eid++)
        {
            for(int pid=0;pid<this->P;pid++)
            {
                getline(fp,line);
                if(stoi(line)==1)
                {
                    this->events[eid].add_period(pid);
                }
            }
        }


        // Track consecutive events
        for(int eid1=0;eid1<this->E;eid1++)
        {
            for(int eid2=0;eid2<this->E;eid2++)
            {
                getline(fp,line);
                if(line=="") break;
                if(stoi(line)==1)
                {
                    this->after_events[eid1].emplace_back(eid2);
                }
                else if(stoi(line)==-1)
                {
                    this->after_events[eid2].emplace_back(eid1);
                }
            }
        }
    }
}

Problem::~Problem() {}

void Problem::set_formulation(string formulation_name)
{
    this->formulation=formulation_name;
}

string Problem::get_formulation()const {return this->formulation;}


double Problem::density()const
{

}

double Problem::room_suitability()const 
{

}

double Problem::average_room_capacity()const
{

}

double Problem::event_period_unavailability()const
{

}

vector <int> Problem::noise_events()const
{

}


std::ostream &operator<<(std::ostream &os,const Problem &p)
{
    os<<"Events:"<<p.E<<endl;
    os<<"Rooms:"<<p.R<<endl;
    os<<"Features:"<<p.F<<endl;
    os<<"Students:"<<p.S<<endl;
    os<<"Periods:"<<p.P<<endl;
    os<<"Density:"<<p.density()<<endl;
    os<<"Room Suitability:"<<p.room_suitability()<<endl;
    os<<"Event period unavailability:"<<p.event_period_unavailability()<<endl;

    os<<endl;
    os<<"==== Events ===="<<endl;
    for(auto &event:p.events)
    {
        os<<event.to_string()<<endl;
    }
    os<<endl<<endl;

    os<<"==== Rooms ===="<<endl;
    for(auto &room:p.rooms)
    {
        os<<room.to_string()<<endl;
    }

    return os;
}
