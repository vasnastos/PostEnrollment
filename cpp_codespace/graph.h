#include <iostream>
#include <vector>
#include <map>
#include <algorithm>
#include "base.h"

using namespace std;


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