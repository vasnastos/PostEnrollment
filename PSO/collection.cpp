# include "collection.hpp"

Collection::Collection() {}

Collection::~Collection() {}

void Collection::add_point(Data &x,double y)
{
    this->xpoint.emplace_back(x);
    this->ypoint.emplace_back(y);
}

std::pair <Data,double> Collection::get_point(int pos)
{
    if(pos<0 || pos>this->xpoint.size())
    {
        return std::pair<Data,double>();
    }
    return  std::make_pair(this->xpoint.at(pos),this->ypoint.at(pos));
}

double Collection::get_distance(Data &xpoint1,Data &xpoint2)
{
    double sum=0.0;
    for(int i=0,t=xpoint1.size();i<t;i++)
    {
        sum+=pow(xpoint1[i]-xpoint2[i],2);
    }
    return sum/xpoint1.size();
}

bool Collection::isPointIn(Data &x,double &y)
{
    for(int i=0,t=this->xpoint.size();i<t;i++)
    {
        if(this->get_distance(x,this->xpoint[i]))
        {
            return true;
        }
    }
    return false;
}


bool Collection::haveGraphMinima(Data &x,double &y,double distance)
{
    for(int i=0,t=this->ypoint.size();i<t;i++)
    {
        if(this->ypoint[i]<y && this->get_distance(x,this->xpoint[i])<distance)
        {
            return true;
        }
    }
    return false;
}

void Collection::resizeInFraction(double fraction)
{
    for(int i=0,t=this->ypoint.size();i<t;i++)
    {
        for(int j=0;j<t-1;j++)
        {
            if(this->ypoint[j+1]<this->ypoint[j])
            {
                double temp=this->ypoint[j];
                this->ypoint[j]=this->ypoint[j+1];
                this->ypoint[j+1]=temp;
                Data tempx=this->xpoint[j];
                this->xpoint[j]=this->xpoint[j+1];
                this->xpoint[j+1]=tempx;
            }
        }
    }
    int new_size=int(fraction*this->xpoint.size());
    this->xpoint.resize(new_size);
    this->ypoint.resize(new_size);
}