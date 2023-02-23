#include <iostream>
#include <vector>
#include <map>
using namespace std;



template <class T>
class Graph
{
    private:
        vector <T> nodes;
    public:
        map <T,pair<T,int>> adjacency_list;
        vector <pair <T,T>> edge_set;

        Graph();
        void add_node(T node);
        void add_edge(T node1,T node2,double weight=-1);
        void add_nodes_from(vector <T> &gnodes);
        void add_edges_from(map <pair<T,T>,double> &gedges);

        bool has_edge(T node1,T node2)const; 
        vector <pair<T,int>> neighbors(T current_node);

        void save(string filename);
        void load(string filename);
};