#include <iostream>
#include <map>
#include <fstream>
#include <sstream>
#include <filesystem>
#include <sstream>
#include <algorithm>
#include <chrono>
#include "stringops.hpp"

using namespace std;
namespace fs=std::filesystem;

enum class Category
{
    TTCOM_2002,
    ITC_2007,
    HARDER_LEWIS_AND_PAECHTER,
    METAHEURISTICS_NETWORK,
    ERR_CAT
};

class DatasetDB
{
    private:
        map <string,string> instances;
    public:
        static DatasetDB *singleton_instance;
        static DatasetDB* get_instance();
        static void flush();
        DatasetDB();
        Category get_category(const string id);
        bool has_precedence_relation(const string dataset_id);
};