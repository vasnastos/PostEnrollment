#include "graph.hpp"

Graph::Graph() {}
void Graph::add_node(int &nodename)
{
    if(find(this->nodes.begin(),this->nodes.end(),nodename)!=this->nodes.end())
    {
        return;
    }
    this->nodes.emplace_back(nodename);
}

void Graph::add_nodes_from(vector <int> &nodeset)
{
    for(auto &node:nodeset)
    {
        this->add_node(node);
    }
}

void Graph::add_edge(int &n1,int &n2,int &weight)
{
    this->neighborhood[n1][n2]=weight;
    this->neighborhood[n2][n1]=weight;

    if(find_if(this->edges.begin(),this->edges.end(),[&](const pair <int,int> &node_pair) {return (node_pair.first==n1 && node_pair.second==n2) || (node_pair.first==n2 && node_pair.second==n1);})==this->edges.end())
    {
        this->edges.emplace_back(make_pair(n1,n2));
    }
}

vector <int> Graph::neighbors(int &n1)
{   
    vector <int> nneighbors;
    if(this->neighborhood.find(n1)==this->neighborhood.end())
    {
        return nneighbors;
    }
    
    for(auto &[neighbor,weight]:this->neighborhood[n1])
    {
        nneighbors.emplace_back(neighbor);
    }
    return nneighbors;
}

int Graph::get_weight(int &n1,int &n2)
{
    if(this->neighborhood.find(n1)==this->neighborhood.end())
    {
        return -1;
    }
    return this->neighborhood[n1][n2];
}

int Graph::density()
{
    return (2.0*this->edges.size())/(this->nodes.size()*(this->nodes.size()-1));
}
