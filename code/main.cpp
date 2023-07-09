#include "tabu_search.hpp"


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

                Solution *solution=new Solution(problem);

                TSSP tabu_search(solution,190);
                tabu_search.solve();

                delete problem;
                delete solution;
            }
        }
};

int main()
{
    Arena arena;
    arena.solve_all();
}