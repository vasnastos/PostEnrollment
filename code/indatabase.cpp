#include "indatabase.hpp"


DatasetDB::DatasetDB()
{
    if(instances.empty())
    {
        fs::path path_to_registries;
        for(const string &x:{"..","instances","descriptive_ds.csv"})
        {
            path_to_registries.append(x);
        }

        vector <string> data;
        fstream fp;
        string line,word;
        fp.open(path_to_registries.string(),std::ios::in);
        if(!fp.is_open())
        {
            cerr<<"File did not open properly("<<path_to_registries.string()<<")"<<endl;
            return;
        }
        while(getline(fp,line))
        {
            stringstream ss(line);
            data.clear();
            while(getline(ss,word,','))
            {
                data.emplace_back(word);
            }
            if(data.size()!=2) continue;
            this->instances[data[0]]=data[1];
        }
        fp.close();
    }
}

Category DatasetDB::get_category(const string id)
{
    if(this->instances.find(id)!=this->instances.end())
    {
        if(this->instances[id]=="TTCOMP-2002")
        {
            return Category::TTCOM_2002;
        }
        else if(this->instances[id]=="ITC-2007")
        {
            return Category::ITC_2007;
        }
        else if(this->instances[id]=="Harder-(Lewis and Paechter)")
        {
            return Category::HARDER_LEWIS_AND_PAECHTER;
        }
        else if(this->instances[id]=="Metaheuristics Network")
        {
            return Category::METAHEURISTICS_NETWORK;
        }
    }

    return Category::ERR_CAT;
}

bool DatasetDB::has_precedence_relation(const string dataset_id)
{
    return this->get_category(dataset_id)==Category::ITC_2007;
}

DatasetDB* DatasetDB::singleton_instance=nullptr;
DatasetDB* DatasetDB::get_instance()
{
    if(DatasetDB::singleton_instance==nullptr)
    {
        DatasetDB::singleton_instance=new DatasetDB();
    }
    return DatasetDB::singleton_instance;
}

void DatasetDB::flush()
{
    delete DatasetDB::singleton_instance;
}