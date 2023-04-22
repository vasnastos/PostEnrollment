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
        map <int,vector <int>> students;

        map <int,vector <int>> event_available_periods;
        map <int,vector <int>> event_available_rooms;
        Graph G;

        static string path_to_datasets;
        static void change_datasets_path(const vector <string> &path_components);

        void read(string filename);
        double density();
        double average_room_suitability();
        double average_room_size();
        double precedence_density();

        string get_id()const;
        void statistics();
};
