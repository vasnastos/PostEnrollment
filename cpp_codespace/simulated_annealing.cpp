#include "simulated_annealing.h"

SimulatedAnnealing::SimulatedAnnealing(Solution &asolution):solution(&asolution) {}
SimulatedAnnealing::~SimulatedAnnealing() {}

void SimulatedAnnealing::solve(int timesol)
{
    map <int,Sol> moves;
    int temperature=1000;
    double alpha=0.9999;
    double start_temperature=1000;
    string move_name;
    map <int,Sol> best_solution=this->solution->solution_set;
    size_t best_cost=this->solution->compute_cost();
    size_t previous_cost,candicate_cost,delta;
    size_t iter_id=0;
    double freeze_temp=1.0;
    uniform_real_distribution<double> metropolis(0,1);
    
    
    auto start_timer=high_resolution_clock::now();
    

    while(true)
    {
        moves=this->solution->select_operator(move_name);
        if(moves.size()==0)
        {
            if(duration_cast<seconds>(high_resolution_clock::now()-start_timer).count()>timesol)
            {
                break;
            }
        }

        previous_cost=this->solution->compute_cost();
        this->solution->reposition(moves);
        candicate_cost=this->solution->compute_cost();
        delta=candicate_cost-previous_cost;
        if(delta<0)
        {
            if(candicate_cost<best_cost)
            {
                cout<<"SA| New best solution found!!!\tS:"<<candicate_cost<<"\tT:"<<temperature<<endl;
                best_solution=this->solution->solution_set;
                best_cost=candicate_cost;
                iter_id=0;
            }
        }
        else if(delta>0)
        {
            if(metropolis(this->solution->mt)<exp(-delta/temperature))
            {
                // Worse solution accepted based on metropolis criterion
                continue;
            }
            this->solution->rollback();
            iter_id++;
        }
        else
        {
            iter_id++;
        }
        temperature*=alpha;
        if(temperature<=freeze_temp)
        {
            // Apply ortools solver
        }

        if(duration_cast<seconds>(high_resolution_clock::now()-start_timer).count()>timesol)
        {
            break;
        }

    }

    cout<<"SA| Procedure exceed after "<<timesol<<" seconds| S:"<<best_cost<<endl;
    this->solution->set_solution(best_solution);
}