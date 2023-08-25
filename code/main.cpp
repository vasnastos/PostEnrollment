#include "tabu_search.hpp"


void scenario1()
{
    /*
        Find an initial solution using tabu search
        3 classes are used
        - Problem
        - Solution
        - TabuSearch
    */
    string filename="i01.tim";
    Problem problem;
    problem.read(filename);
    Solution solution(&problem);
    TSSP tabu_search(&solution,190);
    tabu_search.solve();
    auto solution_map=tabu_search.get_best_solution();
    if(solution_map.empty())
    {
        cout<<"Solution for filename:"<<filename<<endl<<" does not been found by tabu search"<<endl;
    }
    else
    {
        cout<<"Solution found for "<<filename<<" instance"<<endl;
    }
}


int main()
{
    scenario1();
    return 0;
}