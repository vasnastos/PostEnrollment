#pragma once
#include "../solution.hpp"

using namespace std;


using Chromosome=std::vector <int>;
using Population=std::vector <Chromosome>;

class GeneticRoomSelector
{
    private:
        mt19937 eng;
        vector <int> rooms;
        vector <int> events;
        map <int,vector <pair<int,int>>> captured;
        map <int,int> period_solution;
        Solution *solution;
        Population population;
        Chromosome parent;

        size_t max_generations;
        size_t population_size;
        double mutate_rate;
        
    public:
        GeneticRoomSelector(Solution *sol_item);
        void set_event_population(vector <int> &epopulation);
        void set_room_population(vector <int> &rpopulation);
        void set_period_solution(map <int,int> &psolution);

        void generate_initial_population();
        void mutate();
        Chromosome crossover(const Chromosome &parent1,const Chromosome &parent2);
        int calculate_fitness();

        void solve();

        Chromosome get_solution();
};