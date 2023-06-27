#include "indatabase.hpp"
#include "graph.hpp"
#include <set>

using namespace std;
using namespace std::chrono;

#ifdef _WIN32
    const char sep='\\';
#elif __linux__
    const char sep='/';
#endif


struct Event
{
    set <int> features;
    set <int> students;
};

struct Room
{
    int capacity;
    set <int> features;
};



class Problem
{
    private:
        string id;
        vector <Event> events;
        vector <Room> rooms;
        map <int,vector <int>> students;
        Graph G;

    public:
        // public properties
        int E,S,R,F;
        int P;
        int days;
        int periods_per_day;

        map <int,vector <int>> event_available_periods;
        map <int,vector <int>> event_available_rooms;
        map <int,vector<int>> precedence_events;

        static string path_to_datasets;
        static string get_path(string filename);

        Problem();
        void read(string filename,bool full_path=false);
        void create_graph();
        void create_dependencies();
        int common_students(const int &eid1,const int &eid2);

        void set_id(string filename);
        string get_id()const;



        double conflict_density();
};