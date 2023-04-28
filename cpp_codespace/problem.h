#pragma once
#include "base.h"
#include "graph.h"
#include <random>
#include <chrono>

using namespace std;
using namespace std::chrono;



class Problem
{
private:
    string id;
public:
    int E;
    int R;
    int F;
    int S;
    int P;
    int number_of_days;
    int number_of_periods;
    vector <Event> events;
    vector <Room> rooms;
    vector <int> final_periods_per_day;
    map <int, vector <int>> students;

    map <int, vector <int>> event_available_periods;
    map <int, vector <int>> event_available_rooms;
    Graph G;

    static string path_to_datasets;
    static void change_datasets_path(const vector <string>& path_components);

    void read(string filename);

    /*
    Conflict Graph Density=>(2m/n(n-1))
    */
    double density();
    
    /*
    Room Occupancy/Described as RO (suitab) 
    */
    double room_occupancy();

    /*
    Average room Suitable per Event
    */
    double average_room_suitability();
    
    /*
        Average room size
    */
    double average_room_size();
    
    /*
    Precedence density/Refers only to the ITC2007 Instances/P
    */
    double precedence_density();

    /*
    Average Students per Event/SE
    */
    double average_students_per_event();

    /*
    Average Exams per Student/ES
    */
    double average_events_per_student();

    /*
    Average period avilability/TE
    */
    double average_period_availability();

    string get_id()const;
    void statistics();

    // methods for tabu search
    /*
    Find conflicts of an event
    @param even_id:int::The id of the event i want to track conflicts
    */
    int clashe(const int& event_id);
};
