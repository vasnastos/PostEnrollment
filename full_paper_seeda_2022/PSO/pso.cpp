#include "pso.hpp"

PSO::PSO(Problem *p):problem(p),iter(0) {}

PSO::~PSO() {}

void PSO::set_max_iters(size_t i) {this->max_iters=i;}

size_t PSO::get_max_iters()const {return this->max_iters;}

void PSO::set_particle_count(size_t c) {this->particle_count=c;}

size_t PSO::get_particle_count()const {return this->particle_count;}

Data PSO::get_bestx()const {return this->bestx;}

double PSO::get_besty()const {return this->besty;}

bool PSO::terminated()
{
    
}

void PSO::step()
{

}

void PSO::stop()
{

}


