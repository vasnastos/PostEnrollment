#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <string>
#include <algorithm>
#include <cassert>
#include <set>
#include <cmath>
#include "graph.hpp"

using namespace std;

class Event
{
    public:
        int id;
        vector <int> students;
        set <int> features;

        Event(int exam_index);
        void add_student(int sid);
        void add_feature(int fid);
        bool operator==(const int candicate_id);
        string to_string()const;
};

class Room
{
    public:
        int id;
        int capacity;
        set <int> features;
        Room(int room_id);
        Room(int room_id,int room_capacity);
        ~Room();

        void add_feature(int feature_id);
        bool operator==(const int candicate_id);
        string to_string()const;
};

class Problem
{
    private:
        vector <Event> events;
        map <int,vector <int>> students;
        map <int,vector <int>> suitable_rooms;
        map <int,vector <int>> event_periods; 
        map <int,vector <int>> after_events;
        
    public:
        vector <Room> rooms;
        string formulation;
        Graph <int> G;
        int E;
        int F;
        int R;
        int S;
        int P;

        Problem(string filename,string formulationN);
        ~Problem();
        void create_graph();
        
        // setters/getters
        void set_formulation(string formulation_name);
        string get_formulation()const;

        // statistics
        double density()const;
        double room_suitability()const;
        double average_room_capacity()const;
        double event_period_unavailability()const;
        vector <int> noise_events()const;

        friend std::ostream &operator<<(std::ostream &os,const Problem &p);
};