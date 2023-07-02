#include "problem.hpp"


class Arena
{   
    vector <string> datasets;
    public:
        Arena()
        {
            if(Problem::path_to_datasets=="")
            {
                fs::path pth;
                for(const string &x:{"..","instances"})
                {
                    pth.append(x);
                }
                Problem::path_to_datasets=pth.string();
            }

            for(auto &entry:fs::directory_iterator(fs::path(Problem::path_to_datasets)))
            {
                if(endsWith(entry.path().string(),".tim"))
                datasets.emplace_back(entry.path().string());
            }
        }

        void entrance(string filename)
        {
            Problem *problem=new Problem;
            problem->read(filename);
            problem->statistics();
            delete problem;
        }

        void solve_all()
        {
            for(const auto &dataset:datasets)
            {
                Problem *problem=new Problem;
                problem->read(dataset,true);
                problem->statistics();
                delete problem;
            }
        }
};

int main()
{
    Arena arena;
    arena.entrance("i01.tim");
}