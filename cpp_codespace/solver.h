#pragma once
#include <vector>
#include <map>
#include <sstream>
#include "gurobi_c++.h"
#include "problem.h"

using namespace std;

map <int, Sol> initialize_solution(Problem *problem,double timesol);
map <int, Sol> day_by_day(Problem* problem,int day, const map <int, Sol>& solution_hint = {},double timesol=600);
map <int, Sol> days_combined(Problem* problem, vector <int> &days ,const  map <int, Sol>& solution_hint = {});