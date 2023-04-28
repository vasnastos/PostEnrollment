#include "graph.h"

Graph::Graph() {}

void Graph::add_node(int node)
{
    this->nodes.emplace_back(node);
}

void Graph::add_edge(int n1,int n2,int weight)
{
    if(std::find_if(this->edges.begin(),this->edges.end(),[&](const Edge &v) {return (v.node1==n1 && v.node2==n2) || (v.node1==n2 && v.node2==n1);})!=this->edges.end())
    {
        return;
    }

    this->graph_map[n1].emplace_back(Vertex(n2,weight));    
    this->graph_map[n2].emplace_back(Vertex(n1,weight));
    this->edges.emplace_back(Edge(n1,n2));
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

int Graph::number_of_nodes()const {return this->nodes.size();}
int Graph::number_of_edges()const {return this->edges.size();}