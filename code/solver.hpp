#pragma once
#include <vector>
#include <map>
#include <sstream>
#include "gurobi_c++.h"

using namespace std;

map <int, Sol> initialize_solution(Problem *problem,double timesol);