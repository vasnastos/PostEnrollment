#include <iostream>
#include <vector>
#include <map>
#include <filesystem>
#include <fstream>
#include <sstream>
#include "base.h"

using namespace std;
namespace fs=std::filesystem;

class Arena
{
    private:
        map <string,int>  opthub;
        map <string,int> obtained_solutions;
    public:
        Arena();
        ~Arena();

        void refresh();

        void save(map <int,Sol> &solution,int solution_cost,string solution_id);
        void to_csv();
};