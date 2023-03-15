#include "problem.hpp"
#include <numeric>

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
        bool isPointIn(Data &x,double &y);

        std::pair <Data,double> get_point(int pos);
        void replacePoint(int pos,Data &x,double &y);
        bool haveGraphMinima(Data &x,double &y,double distance);
        void get_best_worst_values(double &besty,double &worsty);
        void resizeInFraction(double fraction);
};