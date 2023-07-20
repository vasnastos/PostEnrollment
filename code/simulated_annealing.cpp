#include "simulated_annealing.hpp"

SimulatedAnnealing::SimulatedAnnealing(Solution *solution_obj):solution(solution_obj) {
    this->start_temperature=1000;
    this->freeze_temperature=1.0;
    this->alpha=0.9999;
}

SimulatedAnnealing::~SimulatedAnnealing() {}

bool SimulatedAnnealing::time_elapsed()
{
    auto timestamp=high_resolution_clock::now();
    return duration_cast<seconds>(timestamp-this->start_timer).count()>this->solution_time;
}

void SimulatedAnnealing::solve(size_t elapsed_time)
{
    map <int,Sol> moves;
    map <string,int> status;
    double temperature=this->start_temperature;
    int current_cost,previous_cost,delta,solution_activation_counter;
    uniform_real_distribution <double> metropolis(0,1);
    uniform_real_distribution <double> reheater(0.5,2.0);
    this->start_timer=high_resolution_clock::now();

    status["S"]=0;
    status["B"]=0;

    while(true)
    {
        moves=this->solution->select_random_move();
        if(moves.empty())
        {
            if(this->time_elapsed())
            {
                break;
            }
        }
        previous_cost=this->solution->compute_cost();
        this->solution->reposition(moves);
        current_cost=this->solution->compute_cost();
        delta=current_cost-previous_cost;

        if(delta<0)
        {
            status["S"]++;
            cout<<"SA| New solution found  C:"<<current_cost<<"  T:"<<temperature<<Celsius<<"  D:"<<delta<<endl; 
            this->best_solution=this->solution->get_schedule();
            this->best_cost=current_cost;
        }
        else if(delta>0)
        {
            status["B"]++;
            if(metropolis(this->solution->eng)<exp(-delta/temperature))
            {
                // solution is accepted
            }
            else
            {
                this->solution->rollback();
            }
        }
        else
        {
            status["B"]++;
            solution_activation_counter++;
        }

        temperature*=this->alpha;

        if(temperature<this->freeze_temperature)
        {

            temperature=reheater(this->solution->eng)*start_temperature;
            cout<<"Temperature reheating:"<<temperature<<Celsius<<endl;

            // Activate exact solvers
        }
    }

    cout<<"SA| Procedure ended after "<<this->solution_time<<" seconds"<<endl;
    cout<<"SA| Best Cost:"<<this->best_cost<<endl;
    cout<<"SA| [Moves Info]  Successful:"<< status["S"]  <<"Blank:"<<status["B"]<<endl;
}

map <int,Sol> SimulatedAnnealing::get_best_solution()const
{
    return this->best_solution;
}