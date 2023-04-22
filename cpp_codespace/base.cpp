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

string Instance::get_formulation()const
{
    switch (this->formulation)
    {
    case Formulation::ITC2007:
        return "ITC2007";
        break;
    case Formulation::TTCOMP2002:
        return "ITC2002";
        break;
    case Formulation::MetaheuristicsNetwork:
        return "MetaheuristicsNetwork";
        break;
    case Formulation::HarderLewisPaechter:
        return "HarderLewisPaechter";
        break;
    default:
        return "UNFORMULATED";
        break;
    }
}

string PRF::path_to_form="";
PRF* PRF::_instance=nullptr;

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
    if(!this->instances.empty()) return;
    string line,word;
    fstream fp(PRF::path_to_form);
    vector <string> fdata;
    bool start_line=true;
    while(getline(fp,line))
    {
        if(start_line)
        {
            start_line=false;
            continue;
        }
        fdata.clear();
        stringstream ss(line);
        while(getline(ss,word,','))
        {
            fdata.emplace_back(word);
        }
        this->instances.emplace_back(Instance(replaceString(fdata[0],".tim",""),fdata[2]));
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

void PRF::print()
{
    cout<<"=== Datasets ==="<<endl;
    for(const auto &x:this->instances)
    {
        cout<<x.name<<" "<<x.get_formulation()<<endl;
    }
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

