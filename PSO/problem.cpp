#include "problem.hpp"

Problem::Problem(int n):dimension(n)
{
    this->left.resize(n);
    this->right.resize(n);
    this->besty=1e+100;
    this->function_calls=0;
}

Problem::~Problem() {}
int Problem::get_dimension()const {return this->dimension;}
void Problem::set_left_margin(Data &x) {this->left=x;}
void Problem::set_right_margin(Data &x) {this->right=x;}
Data Problem::get_left_margin()const {return this->left;}
Data Problem::get_right_margin()const {return this->right;}

double Problem::minimize(Data &x)
{
    double y=this->minimize(x);
    if(y<besty)
    {
        besty=y;
        bestx=x;
    }
    this->function_calls++;
    return y;
}

double Problem::gradient_mean_square(Data &x)
{
    Data g=this->gradient(x);
    double s=0.0;
    for(int i=0,t=x.size();i<t;i++)
    {
        s+=pow(g[i],2);
    }
    return s;
}

Data Problem::get_bestx()const
{
    return this->bestx;
}

double Problem::get_besty()const {return this->besty;}

int Problem::get_function_calls()const {return this->function_calls;}

bool Problem::is_point_in(Data &x)
{
    for(int i=0,t=x.size();i<t;i++)
    {
        if(x[i]<this->left[i] || x[i]>this->right[i]) 
            return false;
    }
    return true;
}

bool Problem::isPointIn(Data &x)
{
    for(int i=0,t=x.size();i<t;i++)
    {
        if(x[i]<this->left[i] || x[i]>this->right[i]) return false;
    }
    return true;
}