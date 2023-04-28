#include "problem.h"

void Problem::read(string filename)
{
    // Find path to file
    fs::path fdps(Problem::path_to_datasets);
    fdps.append(filename);

    string line, word;
    vector <string> first_line_data;

    this->id = replaceString(filename, ".tim", "");
    fstream fp;
    fp.open(fdps.string(), std::ios::in);

    if (!fp.is_open())
    {
        cerr << "File:" << fdps.string() << " is not opened" << endl;
        return;
    }

    // read first line
    getline(fp, line);
    stringstream ss(line);

    while (getline(ss, word, ' '))
    {
        first_line_data.emplace_back(word);
    }

    this->E = stoi(first_line_data[0]);
    this->R = stoi(first_line_data[1]);
    this->F = stoi(first_line_data[2]);
    this->S = stoi(first_line_data[3]);

    this->events.resize(this->E);
    this->rooms.resize(this->R);

    // Start data reading
    for (int rid = 0; rid < this->R; rid++)
    {
        getline(fp, line);
        this->rooms[rid].capacity = stoi(line);
    }

    // Event-Student relations
    for (int eid = 0; eid < this->E; eid++)
    {
        for (int sid = 0; sid < this->S; sid++)
        {
            getline(fp, line);
            if (stoi(line) == 1)
            {
                this->events[eid].students.insert(sid);
                this->students[sid].emplace_back(eid);
            }
        }
    }

    // Room-Feature relations
    for (int rid = 0; rid < this->R; rid++)
    {
        for (int fid = 0; fid < this->F; fid++)
        {
            getline(fp, line);
            if (stoi(line) == 1)
            {
                this->rooms[rid].features.insert(fid);
            }
        }
    }

    // Event feature relation
    for (int eid = 0; eid < this->E; eid++)
    {
        for (int fid = 0; fid < this->F; fid++)
        {
            getline(fp, line);
            if (stoi(line) == 1)
            {
                this->events[eid].features.insert(fid);
            }
        }
    }

    // get formulation and if precedence relations are tracked continue to the following mods
    if (PRF::get_instance()->has_precedence_relation(this->id))
    {
        for (int eid = 0; eid < this->E; eid++)
        {
            for (int pid = 0; pid < this->P; pid++)
            {
                getline(fp, line);
                if (stoi(line) == 1)
                {
                    this->event_available_periods[eid].emplace_back(pid);
                }
            }
        }

        // Precedence relations between events
        for (int eid = 0; eid < this->E; eid++)
        {
            for (int eid2 = 0; eid2 < this->E; eid2++)
            {
                getline(fp, line);
                if (line == "") break;
                if (stoi(line) == 1)
                {
                    this->events[eid].precedence_events.emplace_back(eid2);
                }
                else if (stoi(line) == -1)
                {
                    this->events[eid2].precedence_events.emplace_back(eid);
                }
            }
        }
    }

    fp.close();

    // Create event-event relations based on common students
    for (int e1 = 0; e1 < this->E; e1++)
    {
        this->G.add_node(e1);
        for (int e2 = e1 + 1; e2 < this->E; e2++)
        {
            set <int> common_students;
            std::set_intersection(this->events[e1].students.begin(), this->events[e1].students.end(), this->events[e2].students.begin(), this->events[e2].students.end(), std::inserter(common_students, common_students.begin()));
            if (common_students.size() > 0)
            {
                this->G.add_edge(e1, e2, common_students.size());
            }
        }
    }

    // Create room-event availability relations
    for (int eid = 0; eid < this->E; eid++)
    {
        this->event_available_periods[eid] = vector<int>();
        for (int rid = 0; rid < this->R; rid++)
        {
            if (std::includes(this->rooms[rid].features.begin(), this->rooms[rid].features.end(), this->events[eid].features.begin(), this->events[eid].features.end()) && this->rooms[rid].capacity >= this->events[eid].students.size())
            {
                this->event_available_rooms[eid].emplace_back(rid);
            }
        }
    }

    for (int day = 0; day < this->number_of_days; day++)
    {
        this->final_periods_per_day.emplace_back(day * this->number_of_periods + this->number_of_periods - 1);
    }
}

double Problem::density()
{
    // 2n/n(n-1) Graph density
    return 2.0 * this->G.number_of_edges() / (this->G.number_of_nodes() * (this->G.number_of_nodes() - 1));

    // Calculate density based on the general type
    // return this->G.number_of_edges()/this->G.number_of_nodes();
}

double Problem::average_room_suitability()
{
    return static_cast<double>(accumulate(this->event_available_rooms.begin(), this->event_available_rooms.end(), 0, [&](int s, const pair <int, vector <int>>& pav) {return s + pav.second.size(); })) / (this->E);
}

double Problem::room_occupancy()
{
    return accumulate(this->event_available_rooms.begin(), this->event_available_rooms.end(), 0.0, [&](double& s, const pair <int, vector <int>>& vp) {return s + vp.second.size(); }) / static_cast<double>(this->R * this->E);
}

double Problem::average_room_size()
{
    return accumulate(this->rooms.begin(), this->rooms.end(), 0, [&](const int& s, const Room& room) {return s + room.capacity; }) / static_cast<double>(this->R);
}

double Problem::average_students_per_event()
{
    return accumulate(this->events.begin(), this->events.end(), 0.0, [&](const double& s, const Event& event) {return s + event.students.size(); })/(this->E);
}

double Problem::average_events_per_student()
{
    return accumulate(this->students.begin(), this->students.end(), 0.0, [&](const double& s, const vector <int>& es) {return s + es.size(); }) / (this->S);
}

double Problem::average_period_availability()
{
    if (!PRF::get_instance()->has_precedence_relation(this->id))
    {
        return 1.0;
    }

    return accumulate(this->event_available_periods.begin(), this->event_available_periods.end(), 0.0, [&](double& s, const pair <int, vector<int>>& vp) {return s + vp.second.size(); }) / static_cast<double>(this->E * this->P);
}

double Problem::precedence_density()
{
    if (!PRF::get_instance()->has_precedence_relation(this->id)) return 0.0;
    // return 2*accumulate(this->events.begin(),this->events.end(),0,[&](double &s,const Event &e) {return s+e.precedence_events.size();})/this->E*(this->E-1); Graph density
    return accumulate(this->events.begin(), this->events.end(), 0.0, [&](const double& s, const Event& e) {return s + e.precedence_events.size(); }) / this->E;
}

string Problem::get_id()const
{
    return this->id;
}

void Problem::statistics()
{
    cout << endl << endl;
    cout << "==== Statistics ====" << endl;
    cout << "Problem:" << this->id << endl;
    cout << "Events(E):" << this->E << endl;
    cout << "Rooms(R):" << this->R << endl;
    cout << "Features(F):" << this->F << endl;
    cout << "Students(S):" << this->S << endl;
    cout << "Density(CGD):" << this->density() << endl;
    cout << "Average Room Suitability(RS):" << this->average_room_suitability() << endl;
    cout << "Average Room Size(RS):" << this->average_room_size() << endl;
    cout << "Precedence Density(PD):" << this->precedence_density() << endl;
    cout << "Average Students per Event(SE):" << this->average_students_per_event() << endl;
    cout << "Average Events per Student(ES):" << this->average_events_per_student() << endl;
    cout << "Average Period availability per Event(TE):" << this->average_period_availability() << endl;
    cout << endl << endl;
}


string Problem::path_to_datasets = "";

void Problem::change_datasets_path(const vector <string>& path_components)
{
    fs::path fpds(".");
    for (const string& x : path_components)
    {
        fpds.append(x);
    }
    Problem::path_to_datasets = fpds.string();
}

int Problem::clashe(const int& event_id)
{
    return this->G.neighbors(event_id).size();
}
