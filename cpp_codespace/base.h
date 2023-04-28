#include <iostream>
#include <vector>
#include <map>
#include <sstream>
#include <filesystem>
#include <fstream>
#include <set>
#include <algorithm>
#include <numeric>
#include <queue>
#include <filesystem>
#include "stringops.h"


using namespace std;
namespace fs=std::filesystem;

struct Event
{
    set <int> features;
    set <int> students;
    vector <int> precedence_events;
};

struct Room
{
    int capacity;
    set <int> features;
};

enum class Formulation
{
    TTCOMP2002,
    ITC2007,
    HarderLewisPaechter,
    MetaheuristicsNetwork
};


struct Instance
{
    string name;
    Formulation formulation;
    Instance(string n,string f);
    string get_formulation()const;
};

class PRF
{
    private:
        vector <Instance> instances;
    public:
        static string path_to_form;
        static PRF *_instance;
        static void set_path(const vector <string> &components);
        static PRF* get_instance();

        PRF();
        ~PRF();

        void  flush();
        void load();
        void print();
        bool has_precedence_relation(string dataset_id);
        Formulation get_formulation(string dataset_id);
};

struct Sol
{
    int period;
    int room;
    Sol(int p_,int r_);
    Sol(const Sol &sln);
};

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