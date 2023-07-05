#include "genetic_selector.hpp"

GeneticRoomSelector::GeneticRoomSelector(Solution *sol_item):solution(sol_item) {}
void GeneticRoomSelector::set_event_population(vector <int> &epopulation)
{
    this->eng=mt19937(high_resolution_clock::now().time_since_epoch().count());
    this->events=epopulation;
    this->population_size=50;
    this->max_generations=100;
    this->mutate_rate=0.1;

    this->population.resize(this->population_size);
}

void GeneticRoomSelector::set_room_population(vector <int> &rpopulation)
{
    this->rooms=rpopulation;
}

void GeneticRoomSelector::set_period_solution(map <int,int> &psolution)
{
    this->period_solution=psolution;
}

void GeneticRoomSelector::generate_initial_population()
{
    uniform_int_distribution <int> dis(0,this->solution->get_problem()->R-1);
    int failure_counter,random_room;

    for(int i=0;i<this->population_size;i++)
    {
        Chromosome chromosome;
        for(int event_idx=0,t=this->events.size();event_idx<t;event_idx++)
        {
            failure_counter=0;
            random_room=dis(this->eng);
            while(!this->solution->room_availability(this->events[event_idx],this->period_solution[this->events[event_idx]],random_room,this->events) && find_if(this->captured[i].begin(),this->captured[i].end(),[&](const pair <int,int> &ps) {return ps.first==this->period_solution[this->events[event_idx]] && ps.second==random_room;})!=this->captured[i].end())
            {
                random_room=dis(this->eng);
                failure_counter++;
                if(failure_counter==this->rooms.size()) break;
            }
            if(failure_counter==this->rooms.size())
            {
                chromosome.emplace_back(-1);
            }
            else{
                this->captured[i].emplace_back(make_pair(this->period_solution[this->events[event_idx]],random_room));
                chromosome.emplace_back(random_room);
            }
        }
        this->population[i]=chromosome;
    }
}

void GeneticRoomSelector::mutate()
{
    uniform_int_distribution <int> random_chromosome(0,this->population.size()-1);
    uniform_int_distribution <int> dis(0,this->events.size()-1);
    uniform_int_distribution <int> rr(0,this->rooms.size()-1);

    int population_idx=random_chromosome(this->eng);
    int event_idx=dis(this->eng);
    int random_room=rr(this->eng);
    int failure_count=0;

    while(!this->solution->can_be_moved(this->events[event_idx],this->period_solution[this->events[event_idx]],this->events) && find_if(this->captured[population_idx].begin(),this->captured[population_idx].end(),[&](const pair <int,int> &ps) {return ps.first==this->period_solution[this->events[event_idx]] && ps.second==random_room;})==this->captured[population_idx].end())\
    {
        random_room=rr(this->eng);
        failure_count++;
        if(failure_count==this->rooms.size()) return;
    }
    this->population[population_idx][event_idx]=random_room;
}

Chromosome GeneticRoomSelector::crossover(const Chromosome &parent1,const Chromosome &parent2)
{
    uniform_int_distribution <int> dis(0,this->events.size()-1);
    int crossover_point=dis(this->eng);
    Chromosome offspring=parent1;
    for(int i=crossover_point,t=this->events.size();i<t;i++)
    {
        offspring[i]=parent2[i];
    }
    return offspring;
}

int GeneticRoomSelector::calculate_fitness()
{

}

void GeneticRoomSelector::solve()
{

}

Chromosome GeneticRoomSelector::get_solution()
{

}