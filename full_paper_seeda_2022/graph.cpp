#include "graph.hpp"
#include "astring.hpp"


template <class T>
Graph<T>::Graph() {}

template <class T>
void Graph<T>::add_node(T node)
{
    if(find(this->nodes.begin(),this->nodes.end(),nodes)!=this->nodes.end()) return; 
    this->nodes.emplace_back(node);
}


template <class T>
void Graph<T>::add_edge(T node1,T node2,double weight)
{
    if(this->edges.find(make_pair(node1,node2))!=this->edges.end()) return;
    this->adjacency_list[node1].emplace_back(make_pair(node2,weight));
    this->edge_set.emplace_back(make_pair(node1,node2));
}

template <class T>
vector <pair <T,int>> Graph<T>::neighbors(T current_node)
{
    return this->adjacency_list[current_node];
}

template <class T>
void Graph<T>::add_nodes_from(vector <T> &gnodes)
{
    for(auto &x:gnodes)
    {
        this->add_node(x);
    }
}

template <class T>
void Graph<T>::add_edges_from(map <pair<T,T>,double> &gedges);

template <class T>
void Graph<T>::save(string filename)
{
    fstream fp(filename,ios::out);

    fp<<"Nodes:"<<endl;
    for(auto &x:this->nodes)
    {
        fp<<x<<endl;
    }
    fp<<endl;
    fp<<"Edges:"<<endl;
    for(auto &[auto &edge,double weight]:this->edges)
    {
        fp<<"("<<edge.first<<","<<edge.second<<"): "<<weight<<endl;
    }
    fp.close();
}

template <class T>
bool Graph<T>::has_edge(T node1,T node2)const
{
    return find_if(this->edge_set.begin(),this->edge_set.end(),[&](const auto &edge_pair) {return (edge_pair.first==node1 && edge_pair.second==node2) || (edge_pair.first==node2 && edge_pair.second==node1);})==this->edge_set.end();
}

template <class T>
void Graph<T>::load(string filename)
{
    string line,word;
    vector <string> data;
    vector <string> data2;
    string description="";

    fstream fp(filename,ios::in);
    while(getline(fp,line))
    {   
        if(line=="Nodes:")
        {
            description="Nodes";
            continue;
        }
        else if(line=="Edges:")
        {
            description="Edges";
            continue;
        }

        if(line=="") continue;
        else if(line=="Nodes")
        {
            this->nodes.emplace_back(stoi(line));
        }
        else if(line=="Edges")
        {
            data.clear();
            line=replaceString(replaceString(line,"(",""),")");
            stringstream ss(line);
            while(getline(ss,word,','))
            {
                data.emplace_back(word);
            }
            data2.clear();
            stringstream ss2(data[1],':')
            while(getline(ss2,word,':'))
            {
                data2.emplace_back(word);
            }

            this->edges[make_pair(static_cast<T>(data[0]),static_cast<T>(data2[0]))]=std::stod(data2[1]);
        }
    }
    fp.close();
}