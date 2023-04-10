#include <iostream>
#include <vector>
#include <map>
#include <sstream>
#include <filesystem>
#include <fstream>

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
};

class PRF
{
    private:
        vector <Instance> instances;
    public:
        static string path_to_form;
        static PRF *_instance;
        static void set_path(const vector <string> &components);

        PRF();
        ~PRF();

        static PRF& get_instance();
        static void  flush();
        void load();
        bool has_precedence_relation(string dataset_id);
        Formulation get_formulation(string dataset_id);
};