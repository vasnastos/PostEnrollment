#include "../solution.hpp"
#define MUTATE_RATE 0.1
#define MAX_GENERATIONS 100
#define POPULATION_SIZE 50

class GeneticRoomSelector
{
    private:
        vector <int> rooms;
        vector <int> events;
        Solution *solution;
    public:
        GeneticRoomSelector(Solution *sol_item);
        void set_event_population(vector <int> &epopulation);
        void set_room_population(vector <int> &rpopulation);

        

};