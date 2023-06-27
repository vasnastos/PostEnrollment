#include "stringops.hpp"

std::string ltrim(const std::string &s) {
    return std::regex_replace(s, std::regex("^\\s+"), std::string(""));
}
 
std::string rtrim(const std::string &s) {
    return std::regex_replace(s, std::regex("\\s+$"), std::string(""));
}
 
std::string trim(const std::string &s) {
    return ltrim(rtrim(s));
}


std::string replaceString(std::string subject, const std::string& search,const std::string& replace) {
    size_t pos = 0;
    while ((pos = subject.find(search, pos)) != std::string::npos) {
         subject.replace(pos, search.length(), replace);
         pos += replace.length();
    }
    return subject;
}

bool isNumber(const std::string &numberVal)
{
    return regex_match(numberVal,std::regex("-?[0-9]+([\\.][0-9]+)?"));
}

void removeFileExtension(std::string &id)
{
    for(const string &extension:{"csv","txt","data","train","test"})
    {
        if(std::regex_match(id,std::regex(".*\\."+extension+"$")))
        {
            id=replaceString(id,"."+extension,"");
            break;
        }
    }
}

bool endsWith(const std::string& str, const std::string& suffix) {
    if (str.length() < suffix.length()) {
        return false;
    }
    return str.substr(str.length() - suffix.length()) == suffix;
}