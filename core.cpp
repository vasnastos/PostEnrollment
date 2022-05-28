#include <iostream>
#include <fstream>
#include <filesystem>
#include <vector>
#include <sstream>

namespace fs=std::filesystem;


std::string select_file()
{
    std::vector <std::string> datasets;
    fs::path file_path("");
    file_path.append("instances");
    for(auto &dir_entry:fs::directory_iterator(file_path))
    {
        if(fs::is_regular_file(dir_entry))
        {
            datasets.emplace_back(fs::absolute(file_path).string());
        }
    }
    for(int i=0,t=datasets.size();i<t;i++)
    {
        std::cout<<i+1<<"."<<datasets[i]<<std::endl;
    }
    int j;
    std::cout<<"----"<<std::endl;
    std::cout<<"Select dataset:";
    std::cin>>j;
    return datasets[j-1];
}


class Problem
{
    private:
        int nrooms;
        int nstudents;
        int nfeatures;
        int nevents;
        std::vector <int> rooms;
        std::vector <std::vector <int>> students;
        std::vector <std::vector <int>> features;
    
    public:
        static std::string path_to_dataset;
        Problem(int E,int R,int F,int S,std::vector <int> &rooms,std::vector <std::vector <int>> &sts,std::vector <std::vector <int>> &fts):nevents(E),nrooms(R),nstudents(S),nfeatures(F),rooms(rooms),students(sts),features(fts) {}
        ~Problem() {}
        void load_dataset(std::string &ds_name)
        {
            int count_student=0,count_feature=0,student_id=1,file_index=0; 
            std::string line;
            std::vector <int> student_events,event_features;
            std::string filename=Problem::path_to_dataset+ds_name;
            std::fstream fp(filename,std::ios::in);
            if(!fp.is_open())
            {
                std::cerr<<"File did not open"<<std::endl;
                return;
            }
            while(std::getline(fp,line))
            {
                if(file_index==0)
                {
                    std::vector <std::string> data;
                    std::string word;
                    std::stringstream  ss(line);
                    while(std::getline(ss,word,' '))
                    {
                        data.emplace_back(word);
                    }
                    this->nevents=std::stoi(data[0]);
                    this->nrooms=std::stoi(data[1]);
                    this->nfeatures=std::stoi(data[2]);
                    this->nstudents=std::stoi(data[3]);
                    file_index++;
                    continue;
                }
                if(file_index<this->nrooms)
                {
                    this->rooms.emplace_back(std::stoi(line));
                    continue;
                }
                if(student_id!=this->nstudents)
                {
                    if(count_student%this->nevents==0 && count_student!=0)
                    {
                        this->students.emplace_back(student_events);
                        student_events=std::vector <int>();
                        student_id++;
                    }
                    student_events.emplace_back(std::stoi(line));
                }
                else
                {
                    if(count_feature!=0 && count_feature%this->nfeatures==0)
                    {
                        this->features.emplace_back(event_features);
                        event_features=std::vector<int>();
                    }
                    event_features.emplace_back(std::stoi(line));
                    count_feature++;
                }
                file_index++;
            }
            fp.close();
        }
};



std::string Problem::path_to_dataset="instances/";