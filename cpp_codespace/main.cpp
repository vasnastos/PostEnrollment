#include "problem.h"

int main(int argc,char **argv)
{
    PRF::get_instance()->load();
    PRF::get_instance()->print();
    Problem::change_datasets_path({"..","instances"});

    Problem problem;
    problem.read("easy01.tim");
    problem.statistics();


    PRF::get_instance()->flush();
}