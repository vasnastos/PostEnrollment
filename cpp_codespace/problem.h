#include "base.h"
#include <set>
#include <algorithm>
#include <numeric>
#include "stringops.hpp"
#include "graph.h"

using namespace std;


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
        map <int,vector <int>> students;

        map <int,vector <int>> event_available_periods;
        map <int,vector <int>> event_available_rooms;
        Graph G;

        Problem();
        void read(string filename);
        double density();
        double average_room_suitability();
        double average_room_size();
        double precedence_density();
};
