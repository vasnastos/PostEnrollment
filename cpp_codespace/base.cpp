#include "base.h"

Instance::Instance(string n,string f):name(n) {
    if(f=="TTCOMP-2002")
    {
        this->formulation=Formulation::TTCOMP2002;
    }
    else if(f=="ITC-2007")
    {
        this->formulation=Formulation::ITC2007;
    }
    else if(f=="Harder-(Lewis and Paechter)")
    {
        this->formulation=Formulation::HarderLewisPaechter;
    }
    else
    {
        this->formulation=Formulation::MetaheuristicsNetwork;
    }

}

string PRF::path_to_form="";
PRF PRF::*_instance=nullptr;

PRF::PRF()
{
    PRF::set_path({"..","instances","descriptive_ds.csv"});
}

PRF::~PRF() {

}

PRF* PRF::get_instance()
{
    if(PRF::_instance==nullptr)
    {
        PRF::_instance=new PRF;
    }
    return PRF::_instance;
}

void PRF::set_path(const vector <string> &components)
{
    fs::path pth(".");
    for(auto &x:components)
    {
        pth.append(x);
    }
    PRF::path_to_form=pth.string();

}

void PRF::load()
{
    string line,word;
    fstream fp(PRF::path_to_form);
    vector <string> fdata;
    while(getline(fp,line))
    {
        fdata.clear();
        stringstream ss(line);
        while(getline(ss,word,','))
        {
            fdata.emplace_back(word);
        }
        this->instances.emplace_back(Instance(fdata[0],fdata[2]));
    }
    fp.close();
}

void PRF::flush()
{
    delete PRF::_instance;
}

bool PRF::has_precedence_relation(string dataset_id)
{
    auto data_itr=find_if(this->instances.begin(),this->instances.end(),[&](const Instance &instance) {return instance.name==dataset_id;});
    if(data_itr==this->instances.end())
    {
        cerr<<"Dataset:"<<dataset_id<<" not found"<<endl;
        return false;
    }
    return data_itr->formulation==Formulation::ITC2007;
}

Formulation PRF::get_formulation(string dataset_id)
{
    auto data_itr=find_if(this->instances.begin(),this->instances.end(),[&](const Instance &instance) {return instance.name==dataset_id;});
    if(data_itr==this->instances.end())
    {
        cerr<<"Dataset:"<<dataset_id<<" not found"<<endl;
        exit(EXIT_FAILURE);
    }
    return data_itr->formulation;
}

