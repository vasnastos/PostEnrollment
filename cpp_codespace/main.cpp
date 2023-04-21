#include "problem.h"

int main(int argc,char **argv)
{
    Problem problem;
    problem.read("easy01.tim");
    problem.statistics();
}