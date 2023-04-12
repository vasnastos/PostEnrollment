#include <iostream>
#include <vector>
#include <map>

using namespace std;

struct Vertex
{
    int neighbor;
    double weight;
    Vertex(int n2,double w);
};

struct Edge
{
    int node1;
    int node2;
    Edge(int n1,int n2);
};


class NotFoundException : public std::exception {
public:
    const char* what() const noexcept override {
        return "Element not found";
    }
};


class Graph
{
    public:
        vector <int> nodes;
        vector <Edge> edges;
        map <int,vector <Vertex>> graph_map;


        Graph();
        void add_node(int node);
        void add_edge(int n1,int n2,int weight=-1);
        vector <int> neighbors(int n1);

        int get_weight(int n1,int n2);
        int number_of_nodes()const;
        int number_of_edges()const;
};