#include "solver.hpp"

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