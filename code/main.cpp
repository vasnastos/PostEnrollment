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
            cout<<problem->conflict_density()<<endl;
            delete problem;
        }

        void solve_all()
        {
            for(const auto &dataset:datasets)
            {
                Problem *problem=new Problem;
                problem->read(dataset,true);
                cout<<problem->get_id()<<"\tCD:"<<problem->conflict_density()<<endl;
                delete problem;
            }
        }
};

int main()
{
    Arena arena;
    arena.solve_all();
}