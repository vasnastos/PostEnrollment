#include <iostream>
#include <vector>
#include <map>
#include <algorithm>

using namespace std;

class Graph
{
    private:
        vector <int> nodes;
        vector <pair <int,int>> edges;
        map <int,map <int,int>> neighborhood;
    public:
        Graph();
        void add_node(int &nodename);
        void add_nodes_from(vector <int> &nodeset);
        void add_edge(int &n1,int &n2,int &weight);
        vector <int> neighbors(const int &n1);
        int get_weight(int &n1,int &n2);
        double density();
};