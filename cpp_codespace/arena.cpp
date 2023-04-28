#include "arena.h"
#include "stringops.h"
#ifdef _WIN32
    char PATH_SEPARATOR='\\';
#else
    char PATH_SEPARATOR='/';
#endif

Arena::Arena() {
    // Get opthub data
    fs::path pth(".");
    for(const string &x:{"..","instances","descriptive","pe-ctt.csv"})
    {
        pth.append(x);
    }

    fstream fp;
    string line,word;
    fp.open(pth.string(),std::ios::in);
    bool line_start=true;
    vector <string> data;


    while(getline(fp,line))
    {
        if(line_start)
        {
            line_start=false;
            continue;
        }
        
        stringstream ss(line);
        data.clear();
        while(getline(ss,word,','))
        {
            data.emplace_back(word);
        }

        this->opthub[replaceString(data[0],".tim","")]=stoi(data[13]);
    }
    fp.close();

    this->refresh();
}

void Arena::refresh()
{
    // Refresh obtained solutions
    this->obtained_solutions.clear();
    fs::path pth(".");
    for(const string &x:{"..","solutions","arena"})
    {
        pth.append(x);
    }
    

    string full_path,word,registry,dataset_id;
    int objective_score;
    vector <string> path_components;
    for(auto const &dir_entry:fs::recursive_directory_iterator(pth))
    {
        full_path=dir_entry.path().string();
        path_components.clear();
        stringstream ss(full_path);
        while(getline(ss,word,PATH_SEPARATOR))
        {
            path_components.emplace_back(word);
        }
        registry=path_components.at(path_components.size()-1);


        ss=stringstream(registry);
        path_components.clear();
        while(getline(ss,word,'_'))
        {
            path_components.emplace_back(word);
        }

        dataset_id=path_components.at(0);
        objective_score=stoi(path_components.at(1));
        
        if(this->obtained_solutions.find(dataset_id)!=this->obtained_solutions.end())
        {
            if(objective_score<this->obtained_solutions[dataset_id])
            {
                this->obtained_solutions[dataset_id]=objective_score;
            }
        }
        else
        this->obtained_solutions[dataset_id]=objective_score;
    }

}

void Arena::save(map <int,Sol> &solution,int solution_cost,string solution_id)
{
    
}

void Arena::to_csv()
{

}