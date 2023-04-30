#include "solver.h"

map <int, Sol> initialize_solution(Problem *problem,double timesol)
{
	GRBEnv* env = nullptr;
	map <int, map <int, map<int, GRBVar>>> xvars;

	try {
		env = new GRBEnv();
		GRBModel model(*env);
		model.set(GRB_StringAttr_ModelName, "Post_Enrollment_construct_initial_solution_model");
		stringstream vname;
		

		// 1. Set decision variables
		for (int eid = 0; eid < problem->E; eid++)
		{
			for (int rid = 0; rid < problem->R; rid++)
			{
				for (int pid = 0; pid < problem->P; pid++)
				{
					vname.clear();
					vname << "xvar_" << eid << "_" << rid << "_" << pid;
					xvars[eid][rid][pid] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY,vname.str());
				}
			}
		}

		// 2. Each event should be placed at only one period and room
		auto sum = [&](const int& event_id) {
			GRBLinExpr s = 0;
			for (int rid = 0; problem->R; rid++)
			{
				for (int pid = 0; pid < problem->P; pid++)
				{
					s += xvars[event_id][rid][pid];
				}
			}
			return s;
		};

		for (int eid = 0; eid <= problem->E; eid++)
		{
			model.addConstr(sum(eid) == 1, "Only_one_solution_" + to_string(eid));
		}


		// 3. Set the suitable periods and rooms for each event
		for (int eid = 0; eid < problem->E; eid++)
		{
			for (int rid = 0; rid < problem->R; rid++)
			{
				if (find(problem->event_available_rooms[eid].begin(), problem->event_available_rooms[eid].end(), rid) == problem->event_available_rooms[eid].end())
				{
					GRBLinExpr exp = 0;
					for (int pid = 0; pid < problem->P; pid++)
					{
						exp += xvars[eid][rid][pid];
					}
					model.addConstr(exp == 0);
				}
			}

			for (int pid = 0; pid < problem->P; pid++)
			{	
				GRBLinExpr exp = 0;
				for (int rid = 0; rid < problem->R; rid++)
				{
					exp += xvars[eid][rid][pid];
				}
				model.addConstr(exp == 0);
			}
		}

		// 4. A distinct room event pair must only host 1 event
		for (int rid = 0; rid < problem->R; rid++)
		{
			for (int pid = 0; pid < problem->P; pid++)
			{
				GRBLinExpr exp = 0;
				for (int eid = 0; eid < problem->E; pid++)
				{
					exp += xvars[eid][rid][pid];
				}
				model.addConstr(exp <= 1);
			}
		}
		
		vector <int> eneighbors;
		// 5. Neighbor Events must not be placed in the same timesolt
		for (int eid = 0; eid < problem->E; eid++)
		{
			eneighbors = problem->G.neighbors(eid);
			for (auto& neid : eneighbors)
			{
				for (int pid = 0; pid < problem->P; pid++)
				{
					GRBLinExpr exp1= 0,exp2=0;
					for (int rid = 0; rid < problem->R; rid++)
					{
						exp1 += xvars[eid][rid][pid];
						exp2 += xvars[neid][rid][pid];
					}
					model.addConstr(exp1 + exp2 <= 1);
				}
			}
		}

		// Solution parameters		
		model.set(GRB_DoubleParam_TimeLimit, timesol);
		model.set(GRB_IntParam_Threads, atoi(std::getenv("NUMBER_OF_PROCESSORS")));
		model.optimize();
		
		int status = model.get(GRB_IntAttr_Status);
		map <int, Sol> solution;
		if (status != GRB_INFEASIBLE || status == GRB_OPTIMAL)
		{
			bool found_sol;
			for (int eid = 0; eid < problem->E; eid++)
			{
				found_sol = false;
				for (int rid = 0; rid < problem->R; rid++)
				{
					for (int pid = 0; pid < problem->P; pid++)
					{
						if (xvars[eid][rid][pid].get(GRB_DoubleAttr_X) == 1.0)
						{
							solution[eid].period = pid;
							solution[eid].room = rid;
							found_sol = true;
							break;
						}
					}
					if (found_sol)
					{
						break;
					}
				}
			}
		}
		return solution;

	}
	catch (GRBException& e)
	{
		cout << "!!!Error Code:" << e.getErrorCode() << endl;
		cout << e.getMessage() << endl;
	}
	delete env;
}

map <int, Sol> day_by_day(Problem* problem, int day ,const map <int, Sol>& solution_hint,double timesol)
{
	GRBEnv* env = new GRBEnv;
	GRBModel model(*env);
	map <int, map<int, map<int, GRBVar>>> xvars;
	vector <int> eset;
	set <int> students_in_day;

	for (int eid = 0; eid < problem->E; eid++)
	{
		if (solution_hint.at(eid).period % problem->number_of_periods == day)
		{
			eset.emplace_back(eid);
			for (auto& student_id : problem->events[eid].students)
			{
				students_in_day.insert(student_id);
			}
		}
	}
	
	//1. Declare decision variables
	stringstream vname;
	for (auto &eid:eset)
	{
		for (int rid = 0; rid < problem->R; rid++)
		{
			for (int pid = day * problem->number_of_periods; pid < day * problem->number_of_periods + problem->number_of_periods; pid++)
			{
				vname.clear();
				vname << "xvar_" << eid << "_" << rid << "_" << pid;
				xvars[eid][rid][pid] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY, vname.str());
			}
		}
	}

	// 2. Each event should be placed at only one period and room
	for (auto& eid : eset)
	{
		GRBLinExpr exp = 0;
		for (int rid = 0; rid < problem->R; rid++)
		{
			for (int pid = day * problem->number_of_periods; pid < day * problem->number_of_periods + problem->number_of_periods; pid++)
			{
				exp += xvars[eid][rid][pid];
			}
		}
		model.addConstr(exp == 1);
	}

	// 3. Set the suitable periods and rooms for each event
	for (int eid = 0; eid < problem->E; eid++)
	{
		for (int rid = 0; rid < problem->R; rid++)
		{
			if (find(problem->event_available_rooms[eid].begin(), problem->event_available_rooms[eid].end(), rid) == problem->event_available_rooms[eid].end())
			{
				GRBLinExpr exp = 0;
				for (int pid = day * problem->number_of_periods; pid < day * problem->number_of_periods + problem->number_of_periods; pid++)
				{
					exp += xvars[eid][rid][pid];
				}
				model.addConstr(exp == 0);
			}
		}

		for (int pid = day * problem->number_of_periods; pid < day * problem->number_of_periods + problem->number_of_periods; pid++)
		{
			GRBLinExpr exp = 0;
			for (int rid = 0; rid < problem->R; rid++)
			{
				exp += xvars[eid][rid][pid];
			}
			model.addConstr(exp == 0);
		}
	}

	// 4. A distinct room event pair must only host 1 event
	for (int rid = 0; rid < problem->R; rid++)
	{
		for (int pid = day * problem->number_of_periods; pid < day * problem->number_of_periods + problem->number_of_periods; pid++)
		{
			GRBLinExpr exp = 0;
			for (auto &eid:eset)
			{
				exp += xvars[eid][rid][pid];
			}
			model.addConstr(exp <= 1);
		}
	}

	vector <int> eneighbors;
	// 5. Neighbor Events must not be placed in the same timesolt
	for (auto &eid:eset)
	{
		eneighbors = problem->G.neighbors(eid);
		for (auto& neid : eneighbors)
		{
			if (find(eset.begin(), eset.end(), neid) != eset.end())
			{
				for (int pid = 0; pid < problem->P; pid++)
				{
					GRBLinExpr exp1 = 0, exp2 = 0;
					for (int rid = 0; rid < problem->R; rid++)
					{
						exp1 += xvars[eid][rid][pid];
						exp2 += xvars[neid][rid][pid];
					}
					model.addConstr(exp1 + exp2 <= 1);
				}
			}
		}
	}

	// 6. Soft Constraints definition
	map <int, map <int, GRBVar>> consecutive_events;

	// Declare the secondary decision variables
	for (auto& student_id : students_in_day)
	{
		for (int i = 3; i < 10; i++)
		{
			vname.clear();
			vname << "CE_S" << student_id << "_CN" << i;
			consecutive_events[student_id][i] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY, vname.str());
		}
	}

	for (auto& student_id: students_in_day)
	{
		/*
		// Calculate Single event days per student
		GRBLinExpr exp = 0;
		for (auto& event_id : student_events)
		{
			for (int pid = day * problem->number_of_periods; pid < day * problem->number_of_periods + problem->number_of_periods; pid++)
			{
				for (int rid = 0; rid < problem->R; rid++)
				{
					exp += xvars[event_id][rid][pid];
				}
			}
		}

		model.addGenConstrIndicator(single_event_days[student_id][day], 1, exp == 1);
		model.addGenConstrIndicator(single_event_days[student_id][day], 0, exp != 1);
		// End of single event days calculation
		*/

		// Calculate consecutive events
		for (int i = 3; i < 10; i++)
		{
			for (int pid = day * problem->number_of_periods; pid = day * problem->number_of_periods + problem->number_of_periods - i + 1; pid++)
			{
				GRBLinExpr previous = 0;
				if (pid - 1 > day * problem->number_of_periods)
				{
					for (auto& event_id : problem->students[student_id])
					{
						for (int rid = 0; rid < problem->R; rid++)
						{
							previous += xvars[event_id][rid][pid - 1];
						}
					}
				}

				GRBLinExpr current = 0;
				for(auto &event_id:problem->students[student_id])
				{
					for (int rid = 0; rid < problem->R; rid++)
					{
						for (int period_id = pid; period_id < pid + i; period_id++)
						{
							current += xvars[event_id][rid][period_id];
						}
					}
				}

				GRBLinExpr next = 0;
				if (pid + i < day * problem->number_of_periods + problem->number_of_periods)
				{
					for (auto& event_id : problem->students[student_id])
					{
						for (int rid = 0; rid < problem->R; rid++)
						{
							previous += xvars[event_id][rid][pid+i];
						}
					}
				}


				model.addConstr(previous - current + next + consecutive_events[student_id][i] <= -(i - 1));
			}
		}
	}

	//A. Find events which take place in the last timeslot
	GRBLinExpr last_day_score = 0;
	GRBLinExpr sume = 0;
	for (auto& eid : eset)
	{
		sume = 0;
		for (int rid = 0; rid < problem->R; rid++)
		{
			sume += xvars[eid][rid][day * problem->number_of_periods + problem->number_of_periods - 1] * problem->events[eid].students.size();
		}
		last_day_score += sume;
	}
	
	//B. Find Consecutive event cost
	GRBLinExpr consecutive_score = 0;
	for (auto& [student_id, ci_map] : consecutive_events)
	{
		for (auto& [ci_counter, ce_var] : ci_map)
		{
			consecutive_score += ce_var * (ci_counter - 2);
		}
	}

	model.setObjective(consecutive_score+last_day_score);
	model.set(GRB_DoubleParam_TimeLimit, timesol);
	model.set(GRB_IntParam_Threads, atoi(std::getenv("NUMBER_OF_PROCESSORS")));
	model.optimize();

	auto status = model.get(GRB_IntAttr_Status);
	map <int, Sol> solution;
	if (status != GRB_INFEASIBLE || status == GRB_OPTIMAL)
	{
		bool found_sol;
		for (auto eid:eset)
		{
			found_sol = false;
			for (int rid = 0; rid < problem->R; rid++)
			{
				for (int pid = day*problem->number_of_periods; pid < day*problem->number_of_periods+problem->number_of_periods; pid++)
				{
					if (xvars[eid][rid][pid].get(GRB_DoubleAttr_X) == 1.0)
					{
						solution[eid].period = pid;
						solution[eid].room = rid;
						found_sol = true;
						break;
					}
				}
				if (found_sol)
				{
					break;
				}
			}
		}
	}
	delete env;
	return solution;
}


map <int, Sol> days_combined(Problem* problem, vector <int> &days,const  map <int, Sol>& solution_hint = {})
{
	map <int, map <int, map <int, GRBVar>>> xvars;
	vector <int> eset;
	vector <int> periods;

	GRBEnv* env = new GRBEnv;
	GRBModel model(*env);

	for (auto& [event_id, sol_item] : solution_hint)
	{
		if(find(days.begin(),days.end(),sol_item.period%problem->number_of_periods)!=days.end())
			eset.emplace_back(event_id);
	}
	
	for (auto& day : days)
	{
		for (int period = day * problem->number_of_periods; period < day * problem->number_of_periods + problem->number_of_periods; period++)
		{
			periods.emplace_back(period);
		}
	}

	stringstream vname;

	// 1. decision variables
	for (auto& event_id : eset)
	{
		for (int rid = 0; rid < problem->R; rid++)
		{
			for (auto& period_id : periods)
			{
				vname.clear();
				vname << "XV_" << event_id << "_" << rid << "_" << period_id;
				xvars[event_id][rid][period_id] = model.addVar(0.0, 1.0, 0.0, GRB_BINARY, vname.str());
			}
		}
	}

	// 2. Only one period-room set should be dadecated to an event
	for (auto& eid : eset)
	{
		GRBLinExpr exp = 0;
		for (int rid = 0; rid < problem->R; rid++)
		{
			for (auto& period_id : periods)
			{
				exp += xvars[eid][rid][period_id];
			}
		}
		model.addConstr(exp==1);
	}

	// 3. Unvailable periods and rooms / event should be excluded from the final solution
	for (auto& eid : eset)
	{
		for (int rid = 0; rid < problem->R; rid++)
		{
			if (find(problem->event_available_rooms[eid].begin(), problem->event_available_rooms[eid].end(), rid) == problem->event_available_rooms[eid].end())
			{
				GRBLinExpr exp = 0;
				for (auto& period_id : periods)
				{
					exp += xvars[eid][rid][period_id];
				}
				model.addConstr(exp == 0);
			}
		}

		for (auto& period_id : periods)
		{
			if (find(problem->event_available_periods[eid].begin(), problem->event_available_periods[eid].end(), period_id) == problem->event_available_periods[eid].end())
			{
				GRBLinExpr exp = 0;
				for (int rid = 0; rid < problem->R; rid++)
				{
					exp += xvars[eid][rid][period_id];
				}
				model.addConstr(exp == 0);
			}
		}

	}

}