#pragma once
#include <string>
#include <regex>

using namespace std;

std::string ltrim(const std::string &s);
std::string rtrim(const std::string &s);
std::string trim(const std::string &s);
std::string replaceString(std::string subject, const std::string& search,const std::string& replace);
bool isNumber(const std::string &numberVal);
void removeFileExtension(std::string &id);