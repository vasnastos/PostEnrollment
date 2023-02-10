#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <string>
#include <algorithm>
#include <cassert>
#include <set>

using namespace std;

class Event
{
    public:
        int id;
        vector <int> students;
        set <int> features;
        vector <int> periods;
        Event(int exam_index);
        void add_student(int sid);
        void add_feature(int fid);
        void add_period(int pid);
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
        vector <int,vector <int>> suitable_rooms;
        vector <int,vector <int>> event_periods; 
        map <int,vector <int>> after_events;
        
        vector <Room> rooms;
        string formulation;
        int E;
        int F;
        int R;
        int S;
        int P;
    public:
        Problem(string filename,string formulationN);
        ~Problem();
        
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