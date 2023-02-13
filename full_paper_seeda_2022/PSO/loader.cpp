#include "loader.hpp"

std::string String::ltrim(const std::string &s)
{
    return std::regex_replace(s,std::regex("^\\s+"),std::string(""));
}

std::string String::rtrim(const std::string &s)
{
    return std::regex_replace(s,std::regex("\\s+$"),std::string(""));
}

std::string String::trim(const std::string &s)
{
    return ltrim(rtrim(s));
}

std::string String::replace(std::string subject,const std::string &sourcest,const std::string &replacest)
{
    size_t pos=0;
    while((pos=subject.find(sourcest,pos))!=std::string::npos)
    {
        subject.replace(pos,sourcest.length(),replacest);
        pos+=replacest.length();
    }
    return subject;
}

Loader::Loader(std::string filename) {
    std::string line,word;
    std::vector <std::string> ldata;


    std::fstream fp;
    fp.open(filename,std::ios::in);
    if(!fp.is_open())
    {
        std::cerr<<"Filename:"<<filename<<" does not exist"<<std::endl;
        return;
    }
    while(std::getline(fp,line))
    {
        line=String::trim(line);
        ldata.clear();
        std::stringstream ss(line);
        while(std::getline(ss,word,'\t'))
        {
            ldata.emplace_back(word);
        }
        
        this->data.emplace_back(std::make_pair(std::stod(ldata[0]),std::stod(ldata[1])));
    }
    fp.close();
}

