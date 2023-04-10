#include "graph.h"

Vertex::Vertex(int n2,double w):neighbor(n2),weight(w)  {}

Graph::Graph() {}

void Graph::add_node(int node)
{
    this->nodes.emplace_back(node);
}

void Graph::add_edge(int n1,int n2,int weight=-1)
{
    this->graph_map[n1].emplace_back(Vertex(n2,weight));    
    this->graph_map[n2].emplace_back(Vertex(n1,weight));
}

vector <int> Graph::neighbors(int n1)
{
    vector <int> nn_set;
    for(auto &vertex:this->graph_map[n1])
    {
        nn_set.emplace_back(vertex.neighbor);
    }
    return nn_set;
}

int Graph::get_weight(int n1,int n2)
{
    try
    {
        if(this->graph_map.find(n1)!=this->graph_map.end())
        {
            auto vertex=std::find_if(this->graph_map[n1].begin(),this->graph_map[n1].end(),[&](const Vertex &v1) {return v1.neighbor==n2;});
            if(vertex!=this->graph_map[n1].end())
            {
                return vertex->weight;
            }
            else
            {
                throw NotFoundException();
            }
        }
        else
            throw NotFoundException();
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return -1;
    }
}