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