#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <regex>
#include <algorithm>
#include <string>



class String
{
    public:
        static std::string ltrim(const std::string &s);
        static std::string rtrim(const std::string &s);
        static std::string trim(const std::string &s);
        static std::string replace(std::string subject,const std::string &sourcest,const std::string &replacest);
};


class Loader
{
    private:
        std::vector <std::pair <double,double>> data;
    public:
        Loader(std::string filename);
        ~Loader();

        std::vector <std::pair <double,double>> get_data();
};