#include <iostream>
#include <vector>
#include <cstdlib>
#include <cmath>

typedef std::vector <double> Data;
typedef std::vector <Data> Matrix;

class Problem
{
    int dimension;
    Data left,right;
    Data bestx;
    double besty;
    int function_calls;
    public:
        Problem(int n);
        ~Problem();
        int get_dimension()const;
        void set_left_margin(Data &x);
        void set_right_margin(Data &x);
        Data get_left_margin()const;
        Data get_right_margin()const;

        virtual double minimize_function()=0;
        virtual Data gradient(Data &x)=0;

        double minimize(Data &x);
        double gradient_mean_square(Data &x);
        Data get_bestx()const;
        double get_besty()const;

        int get_function_calls()const;
        bool is_point_in(Data &x);
};