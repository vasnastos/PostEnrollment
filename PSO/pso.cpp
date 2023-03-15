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
    double miny,maxy;
}

void PSO::step()
{
    this->iter++;
    for(int i=0;i<this->particle_count;i++)
    {
        pair <Data,double> xpoint1=this->particle.get_point(i);
        pair <Data,double> velocity_xpoint1=this->velocity.get_point(i);

        pair <Data,double> best_xpoint=this->bestParticle.get_point(i);
        int n=this->problem->get_dimension();

        this->inertia=0.5 + (rand()*1.0/RAND_MAX)/2.0;

        for(int j=0;j<n;j++)
        {
            double r1=rand()*1.0/RAND_MAX;
            double r2=rand()*1.0/RAND_MAX;

            velocity_xpoint1.first[j]=this->inertia * velocity_xpoint1.first[j]+r1*(xpoint1.first[j]-best_xpoint.first[j])+r2*(xpoint1.first[j]-this->bestx[j]);
        }

        this->velocity.replacePoint(i,velocity_xpoint1.first,velocity_xpoint1.second);
        for(int j=0;j<n;j++)
        {
            xpoint1.first[j]=xpoint1.first[j] + velocity_xpoint1.first[j];
        }

        if(!this->problem->isPointIn(xpoint1.first)) continue; //skip
        
        

    }

}

void PSO::stop()
{

}


