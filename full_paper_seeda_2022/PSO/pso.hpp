#include "pso.hpp"

class PSO
{
    Problem *problem;
    size_t particle_count;
    size_t iter;
    size_t max_iters;
    double inertia;
    double besty;
    Data bestx;
    public:
        PSO(Problem *p);
        ~PSO();
        void set_max_iters(size_t i);
        size_t get_max_iters()const;
        void set_particle_count(size_t c);
        size_t get_particle_count()const;
        Data get_bestx()const;
        double get_besty()const;
        bool terminated();
        void step();
        void stop();
};