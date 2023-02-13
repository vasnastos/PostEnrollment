#include "problem.hpp"

class Collection
{
    private:
        Matrix xpoint;
        Data ypoint;
    public:
        Collection();
        ~Collection();

        void add_point(Data &x,double y);
        double get_distance(Data &xpoint1,Data &xpoint2);
        size_t get_size()const;
        std::pair <Data,double> get_point(int pos);
        void get_best_worst_values();
};