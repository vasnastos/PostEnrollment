#include "problem.hpp"

string Problem::path_to_datasets="";

string Problem::get_path(string filename)
{
    fs::path filepath;
    filepath.append(Problem::path_to_datasets);
    filepath.append(filename);
    return filepath.string();
}

Problem::Problem()
{
    this->days=5;
    this->periods_per_day=9;
    this->P=45;
}

void Problem::read(string filename,bool full_path)
{
    this->set_id(filename);
    fstream fp;
    if(!full_path)
    fp.open(Problem::get_path(filename),std::ios::in);
    else 
    fp.open(filename,std::ios::in);


    if(!fp.is_open())
    {
        cerr<<"File did not open properly("<<filename<<")"<<endl;
        return;
    }

    vector <string> data;
    string line_data,word;

    getline(fp,line_data);
    stringstream ss(line_data);
    cout<<line_data<<endl;
    while(getline(ss,word,' '))
    {
        data.emplace_back(word);
    }
    if(data.size()!=4) return;

    this->E=stoi(data[0]);
    this->R=stoi(data[1]);
    this->F=stoi(data[2]);
    this->S=stoi(data[3]);

    this->events.resize(this->E);
    this->rooms.resize(this->R);

    for(int i=0;i<this->R;i++)
    {
        getline(fp,line_data);
        this->rooms[i].capacity=stoi(line_data);
    }

    // Student-event relation
    // for 3 students and 4 events the student-event adjacency table will be
    //0 1 0 0 1 1 0 1 0 1 1 
    //      e1  e2  e3  e4
    // s1   0   1   0   0
    // s2   1   1   0   1
    // s3   1   0   1   1
    for(int sid=0;sid<this->S;sid++)
    {
        for(int eid=0;eid<this->E;eid++)
        {
            getline(fp,line_data);
            if(stoi(line_data)==1)
            {
                this->events[eid].students.insert(sid);
                this->students[sid].emplace_back(eid);
            }
        }
    }

    // Room-Feature Relation
    for(int rid=0;rid<this->R;rid++)
    {
        for(int fid=0;fid<this->F;fid++)
        {
            getline(fp,line_data);
            if(stoi(line_data)==1)
            {
                this->rooms[rid].features.insert(fid);
            }
        }
    }

    // Event-feature ralation
    for(int eid=0;eid<this->E;eid++)
    {
        for(int fid=0;fid<this->F;fid++)
        {
            getline(fp,line_data);
            if(stoi(line_data)==1)
            {
                this->events[eid].features.insert(fid);
            }
        }
    }


    // Event period relations and precedence relations
    if(DatasetDB::get_instance()->has_precedence_relation(this->id))
    {
        for(int eid=0;eid<this->E;eid++)
        {
            for(int pid=0;pid<this->P;pid++)
            {
                getline(fp,line_data);
                if(stoi(line_data)==1)
                {
                    this->event_available_periods[eid].emplace_back(pid);
                }
            }
        }
        for(int eid=0;eid<this->E;eid++)
        {
            for(int eid2=0;eid2<this->E;eid2++)
            {
                getline(fp,line_data);
                if(line_data=="")
                {
                    break;
                }
                if(eid==eid2) continue;

                if(stoi(line_data)==1)
                {
                    this->precedence_events[eid].emplace_back(eid2);
                }
                else if(stoi(line_data)==-1)
                {
                    this->precedence_events[eid2].emplace_back(eid);
                }
            }
        }
    }
    fp.close();

    // Generate Graph and dependencies
    this->create_graph();
    this->create_dependencies();
}


void Problem::set_id(string filename)
{
    stringstream ss(filename);

    vector <string> data;
    string word;
    while(getline(ss,word,sep))
    {
        data.emplace_back(word);
    }

    this->id=data.at(data.size()-1);
}

string Problem::get_id()const
{
    return this->id;
}

int Problem::common_students(const int &eid1,const int &eid2)
{
    vector <int> intersector;
    std::set_intersection(this->events[eid1].students.begin(),
                          this->events[eid1].students.end(),
                          this->events[eid2].students.begin(),
                          this->events[eid2].students.end(),
                          std::back_inserter(intersector));
    return intersector.size();

}

void Problem::create_graph()
{
    // add nodes
    for(int eid=0;eid<this->E;eid++)
    {
        this->G.add_node(eid);
    }

    int cs;
    for(int eid1=0;eid1<this->E;eid1++)
    {
        for(int eid2=eid1+1;eid2<this->E;eid2++)
        {
            cs=this->common_students(eid1,eid2);
            if(cs>0)
            {
                this->G.add_edge(eid1,eid2,cs);
            }
        }
    }

}

void Problem::create_dependencies()
{
    for(int eid=0;eid<this->E;eid++)
    {
        for(int rid=0;rid<this->R;rid++)
        {
            if(std::includes(this->rooms[rid].features.begin(),this->rooms[rid].features.end(),this->events[eid].features.begin(),this->events[eid].features.end()) && this->events[eid].students.size()<=this->rooms[rid].capacity)
            {
                this->event_available_rooms[eid].emplace_back(rid);
            }
        }
    }

    // 1-1 egde meaning that if e1 and e2 has no common students and can be placed in exact one common room then an edge assembles between the
    // two events
    int custom_weight=1;
    for(int eid=0;eid<this->E;eid++)
    {
        for(int eid2=eid+1;eid2<this->E;eid2++)
        {
            if((this->event_available_rooms[eid].size()==1 && this->event_available_periods[eid2].size()==1) && this->event_available_rooms[eid]==this->event_available_rooms[eid2])
            {
                this->G.add_edge(eid,eid2,custom_weight);
            }
        }
    }

}

double Problem::conflict_density()
{
    // Graph density 2m/(N(N-1))
    return this->G.density();
}