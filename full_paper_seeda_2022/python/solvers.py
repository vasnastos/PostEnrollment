import logging,os,random,math
import pickle
import gurobipy as gp
import docplex.cp.model as cpx
from time import time
from base import Problem,Core,Configuration
from ortools.sat.python import cp_model
from itertools import combinations
from ps_solution import Solution

class Mathematical_Solver:
    @staticmethod
    def generate_solution(problem:Problem,verbose=False,time_limit=600,solver_type='cpsat'):
        if solver_type == 'cpsat':
            model=cp_model.CpModel()
            dparams={(event_id,room_id,period_id):model.NewBoolVar(name=f'decision_var_{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(Core.P)}

            # Disable all the unavailability variables
            for event_id in range(problem.E):
                for room_id in range(problem.R):
                    if room_id in problem.event_rooms[event_id]: continue 
                    model.Add(sum([dparams[(event_id,room_id,period_id)] for period_id in range(Core.P)])==0)
                for period_id in range(Core.P):
                    if period_id in problem.event_periods[event_id]:  continue
                    model.Add(sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0)
            
            for event_id in range(problem.E):
                model.Add(sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])==1)
            
            for room_id in range(problem.R):
                for period_id in range(Core.P):
                    model.Add(
                        sum([dparams[(event_id,room_id,period_id)] for event_id in range(problem.E)])<=1
                    )

            for event_id in range(problem.E):
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in range(Core.P):
                        if period_id  not in problem.event_periods[event_id] or period_id  not in problem.event_periods[event_id2]: continue
                        model.Add(
                            sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R)])
                            +sum([dparams[(event_id2,room_id,period_id)] for room_id in range(problem.R)])
                            <=1
                        )
            
            if problem.formulation=='full':
                for event_id in range(problem.E):
                    for event_id2 in problem.after_events[event_id]:
                        model.Add(
                            sum([dparams[(event_id,room_id,period_id)] for room_id in problem.rooms for period_id in range(Core.P)])
                            <sum([dparams[(event_id2,room_id,period_id)] for room_id in problem.rooms for period_id in range(Core.P)]) 
                        )
            
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=time_limit
            solver.parameters.num_search_workers = os.cpu_count()
            solver.parameters.log_search_progress=verbose
            status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
            esol={}
            if status==cp_model.FEASIBLE or status==cp_model.OPTIMAL:
                for (event_id,room_id,period_id),dvar in dparams.items():
                    if solver.Value(dvar)==1:
                        esol[event_id]=(period_id,room_id)
            return esol
        
        elif solver_type=='cplex':
            model=cpx.CpoModel()
            xvars={(event_id,room_id,period_id):model.binary_var(name=f'ecombination_{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}

            for event_id in range(problem.E):
                for room_id in range(problem.R):
                    if room_id in problem.event_rooms[event_id]: continue
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for period_id in range(Core.P)])==0
                    )
                
                for period_id in range(Problem.P):
                    if period_id in problem.event_periods[event_id]: continue
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0
                    )
                
            for event_id in range(Problem.E):
                model.add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])==1
                )
            
            for room_id in range(problem.R):
                for period_id in range(problem.P):
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in range(problem.E)])<=1
                    )
            
            for event_id in range(problem.E):
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in range(Core.P):
                        if period_id in problem.event_periods[event_id] or period_id in problem.event_periods[event_id]: continue
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)                                
                            ])
                            +sum([
                                xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)
                            ])
                            <=1
                        ) 
            
            if problem.formulation=="full":
                for event_id in range(problem.E):
                    for event_id2 in problem.after_events[event_id]:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(Core.P)
                            ])
                            <sum([
                                xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(Core.P)
                            ])
                        )
            
            params=cpx.CpoParameters()
            params.TimeLimit=time_limit
            params.Workers=os.cpu_count()
            params.LogVerbosity=True

            solver=model.solve(params=params)
            esol={}
            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1: 
                        esol[event_id]=(period_id,room_id)
            return esol

        elif solver_type=='gurobi':
            model=gp.Model("mip_model")
            dparams=model.addVars([(event_id,room_id,period_id) for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(Core.P)],vtype=gp.GRB.BINARY)

            # Disable all the unavailability variables
            for event_id in range(problem.E):
                for room_id in range(problem.R):
                    if room_id in problem.event_rooms[event_id]: continue 
                    model.addConstr(sum([dparams[(event_id,room_id,period_id)] for period_id in range(Core.P)])==0)
                for period_id in range(Core.P):
                    if period_id in problem.event_periods[event_id]:  continue
                    model.addConstr(sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0)
            
            for event_id in range(problem.E):
                model.addConstr(sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])==1)
            
            for room_id in range(problem.R):
                for period_id in range(Core.P):
                    model.addConstr(
                        sum([dparams[(event_id,room_id,period_id)] for event_id in range(problem.E)])<=1
                    )

            for event_id in range(problem.E):
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in range(Core.P):
                        if period_id  not in problem.event_periods[event_id] or period_id  not in problem.event_periods[event_id2]: continue
                        model.addConstr(
                            sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R)])
                            +sum([dparams[(event_id2,room_id,period_id)] for room_id in range(problem.R)])
                            <=1
                        )
            
            if problem.formulation=='full':
                for event_id in range(problem.E):
                    for event_id2 in problem.after_events[event_id]:
                        x=model.addVar(vtype=gp.GRB.BINARY)
                        model.addConstr(
                            sum([dparams[(event_id,room_id,period_id)]*period_id for room_id in problem.rooms for period_id in range(Core.P)])
                            <=sum([dparams[(event_id2,room_id,period_id)]*period_id for room_id in problem.rooms for period_id in range(Core.P)]) 
                        )
            
            model.optimize()
            
            esol={}
            for (event_id,room_id,period_id),dvar in dparams.items():
                if dvar.X==1:
                    esol[event_id]=(period_id,room_id)
            return esol

    @staticmethod
    def day_by_day(problem:Problem,eset=[],day=0,initial_solution=None,solver_type='cpsat',time_limit=80):
        periods=list(range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day))
        if solver_type=='cpsat':
            model=cp_model.CpModel()
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'decision_variable_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in problem.rooms for period_id in periods}

            if initial_solution: 
                for event_id,(period_id,room_id) in initial_solution.items():
                    model.AddHint(xvars[(event_id,room_id,period_id)],1)

            for event_id in eset:
                for room_id in problem.rooms.keys():
                    if room_id in problem.event_rooms[event_id]: continue 
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                    )

                for period_id in periods:
                    if period_id in problem.event_periods[event_id]: continue
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])==0
                    )
                
            
            for event_id in eset:
                model.Add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys() for period_id in periods])==1
                )
            
            for room_id in problem.rooms.keys():
                for period_id in periods:
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                    )      
            
            for event_id in eset: 
                for event_id2 in list(problem.G.neighbors(event_id)):
                    if event_id2 not in eset: continue
                    for period_id in periods:
                        if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])
                            +sum([xvars[(event_id2,room_id,period_id)] for room_id in problem.rooms.keys()])
                            <=1
                        )
            
            if problem.formulation=='full':
                for event_id in eset:
                    for event_id2 in problem.after_events[event_id]:
                        if event_id2 not in eset: continue
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])
                            <sum([xvars[(event_id2,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])
                        )
            
            ecombinations={frozenset(x):problem.event_combinations[frozenset(x)] for x in combinations(eset,3) if frozenset(x) in problem.event_combinations}
            combination_vars={ecombination:model.NewBoolVar(name=f'event_combinations_{ecombination}') for ecombination in ecombinations}
            for ecombination in ecombinations:
                for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                    model.Add(
                        sum([xvars[(event_id,room_id,current_period)] for event_id in ecombination for room_id in problem.rooms.keys() for current_period in range(period_id,period_id+3)])
                        <=2+combination_vars[ecombination]
                    )

            last_period_of_day=day*Core.periods_per_day+Core.periods_per_day-1
            objective=[
                sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations]),
                sum([len(problem.events[event_id]['S'])*xvars[(event_id,room_id,last_period_of_day)] for event_id in eset for room_id in problem.rooms.keys()])
            ]

            model.Minimize(sum(objective))
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = time_limit
            solver.parameters.num_search_workers = os.cpu_count()
            status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
            esol={}
            if status==cp_model.OPTIMAL or status==cp_model.FEASIBLE:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1: 
                        esol[event_id]=(period_id,room_id)
            return esol

        elif solver_type=='cplex':
            model=cpx.CpoModel()
            xvars={(event_id,room_id,period_id):model.binary_var(name=f'{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in problem.rooms for period_id in periods}

            if initial_solution:
                stp=model.create_empty_solution()
                for event_id in eset:
                    stp[event_id]=initial_solution[event_id]
                model.set_starting_point(stp)

            for event_id in eset:
                for room_id in problem.rooms:
                    if room_id not in problem.event_rooms[event_id]: 
                        model.add(
                            sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                        )

                for period_id in periods:
                    if period_id in problem.event_periods[event_id]:
                        model.add(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])==0
                        )
                
            
            for event_id in eset:
                model.add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys() for period_id in periods])==1
                )
            
            for room_id in problem.rooms.keys():
                for period_id in periods:
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                    )   
            
            for event_id in eset: 
                for event_id2 in problem.G.neighbors(event_id):
                    if event_id2 not in eset: continue
                    for period_id in periods:
                        if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                        model.add(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])
                            +sum([xvars[(event_id2,room_id,period_id)] for room_id in problem.rooms.keys()])
                            <=1
                        )
            
            if problem.formulation=='full':
                for event_id in eset:
                    for event_id2 in problem.after_events[event_id]:
                        if event_id2 not in eset: continue
                        model.add(
                            sum([xvars[(event_id,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])
                            <sum([xvars[(event_id2,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])
                        )
            
            ecombinations={frozenset(x):problem.event_combinations[frozenset(x)] for x in combinations(eset,3) if frozenset(x) in problem.event_combinations}
            combination_vars={ecombination:model.binary_var(name=f'event_combinations_{ecombination}') for ecombination in ecombinations}
            for ecombination in ecombinations:
                for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                    model.add(
                        sum([xvars[(event_id,room_id,current_period)] for event_id in ecombination for room_id in problem.rooms.keys() for current_period in range(period_id,period_id+3)])
                        <=2+combination_vars[ecombination]
                    )
            last_period_of_day=day*Core.periods_per_day+Core.periods_per_day-1
            objective=[
                sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations])
                +sum([len(problem.events[event_id]['S'])*xvars[(event_id,room_id,last_period_of_day)] for event_id in eset for room_id in problem.rooms.keys()])
            ]

            model.minimize(sum(objective))
            params=cpx.CpoParameters()
            params.TimeLimit=time_limit
            params.Workers=os.cpu_count()
            solver=model.solve(params=params)
            esol={}
            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1: 
                        esol[event_id]=(period_id,room_id)
            return esol
        elif solver_type=='gurobi':
            try:
                model=gp.Model("mip_solver_day_by_day")
                xvars=model.addVars([(event_id,room_id,period_id) for event_id in eset for room_id in range(problem.R) for period_id in periods],vtype=gp.GRB.BINARY)
                
                if initial_solution:
                    for event_id,(period_id,room_id) in initial_solution.items():
                        model.VarHintVal(xvars[(event_id,room_id,period_id)],1)

                for event_id in range(problem.E):
                    for room_id in range(problem.R):
                        if room_id in problem.event_rooms[event_id]: continue
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                        )
                    
                    for period_id in periods:
                        if period_id in problem.event_periods[event_id]: continue
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0
                        )
                    
                for event_id in eset:
                    model.addConstr(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in periods])==1
                    )

                for room_id in range(problem.R):
                    for period_id in periods:
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                        )
                
                for event_id in eset:
                    for event_id2 in problem.G.neighbors(event_id):
                        if event_id2 not in eset: continue
                        for period_id in periods:
                            if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                            model.addConstr(
                                sum([xvars[(event_id,room_id,period_id)] for event_id in eset for room_id in range(problem.R)])
                                +sum([xvars[(event_id,room_id,period_id)] for event_id in eset for room_id in range(problem.R)])
                                <=1
                            )
                
                if problem.formulation=="full":
                    for event_id in eset:
                        for event_id2 in problem.after_events[event_id]:
                            if event_id2 not in eset:
                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                    <=sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                )

                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])!=sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                )


                ecombinations={frozenset(x):problem.event_combinations[frozenset(x)] for x in combinations(eset,3) if frozenset(x) in problem.event_combinations}
                combination_vars=model.addVars(ecombinations,vtype=gp.GRB.BINARY)
                for ecombination in ecombinations:
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                        model.addConstr(
                            sum([xvars[(event_id,room_id,current_period)] for event_id in ecombination for room_id in problem.rooms.keys() for current_period in range(period_id,period_id+3)])
                            <=2+combination_vars[ecombination]
                        )
                last_period_of_day=day*Core.periods_per_day+Core.periods_per_day-1
                objective=[
                    sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations]),
                    sum([len(problem.events[event_id]['S'])*xvars[(event_id,room_id,last_period_of_day)] for event_id in eset for room_id in problem.rooms.keys()])
                ]

                model.setObjective(sum(objective),gp.GRB.MINIMIZE)
                model.optimize()

                esol={}
                for (event_id,room_id,period_id),v in xvars.items():
                    if v.X==1: 
                        esol[event_id]=(period_id,room_id)
                return esol
                


            except gp.GurobiError as e:
                print('Error code ' + str(e.errno) + ': ' + str(e))

            except AttributeError:
                print('Encountered an attribute error') 

    @staticmethod
    def days_combined_solver(problem:Problem,eset=[],days=[],initial_solution=None,time_limit=600,solver_type='cpsat'):
        periods=[period_id for day in days for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)]
        ecombinations={frozenset(x):problem.event_combinations[frozenset(x)] for x in combinations(eset,3) if frozenset(x) in problem.event_combinations}
        symmetrical_event_difference=set(problem.events)-set(eset)
        partial_identical_students=dict()
        for events in problem.students.values():
            student_events=set(events)-symmetrical_event_difference
            partial_identical_students[frozenset(student_events)]=partial_identical_students.get(frozenset(student_events),0)+1


        if solver_type=='cpsat':
            model=cp_model.CpModel()
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in problem.rooms.keys() for period_id in periods}

            if initial_solution:
                for event_id in eset:
                    model.AddHint(xvars[(event_id,initial_solution[event_id][1],initial_solution[event_id][0])],1)

            for event_id in eset:
                for room_id in problem.rooms.keys():
                    if room_id in problem.event_rooms[event_id]: continue
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                    )
                
                for period_id in periods:
                    if period_id in problem.event_periods[event_id]: continue
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])==0
                    )
            
            for event_id in eset:
                model.Add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys() for period_id in periods])==1
                )
            
            for room_id in problem.rooms.keys():
                for period_id in periods:
                    model.Add(
                        sum([xvars[event_id,room_id,period_id] for event_id in eset])<=1
                    )
            
            for event_id in eset:
                for event_id2 in problem.after_events[event_id]:
                    if event_id2 in eset:
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in problem.rooms.keys() for period_id in periods])
                            <sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in problem.rooms.keys() for period_id in periods])
                        )
                    else:
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])<initial_solution[event_id2][0]
                        )
            

            single_events={(student_events,day):model.NewBoolVar(name=f'event_set_{student_events}_day_{day}') for student_events in partial_identical_students for day in days}
            combination_vars={ecombination:model.NewBoolVar(name=f'combination_{ecombination}') for ecombination in ecombinations}

            # Single day events
            for student_events in partial_identical_students:
                for day in days:
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in problem.rooms.keys() for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)])==1
                    ).OnlyEnforceIf(single_events[(student_events,day)])

                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in problem.rooms.keys() for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)])!=1
                    ).OnlyEnforceIf(single_events[(student_events,day)].Not())

            # Consecutive events
            for ecombination in ecombinations:
                for day in days:
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                        model.Add(
                            sum([xvars[(event_id,room_id,pcurr)] for event_id in ecombination for room_id in problem.rooms.keys() for pcurr in range(period_id,period_id+3)])
                            <=2+combination_vars[ecombination]
                        )
            
            last_periods_of_days=[day*Core.periods_per_day+Core.periods_per_day-1 for day in days]

            objective=[
                sum([single_events[(student_events,day)]*partial_identical_students[student_events] for student_events in list(partial_identical_students.keys()) for day in days]),
                sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations]),
                sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in eset for room_id in problem.rooms.keys() for period_id in last_periods_of_days])
            ]

            model.Minimize(sum(objective))
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=time_limit
            solver.parameters.num_search_workers=os.cpu_count()
            solver.parameters.log_search_progress=True
            status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
            esol={}
            if status==cp_model.FEASIBLE or status==cp_model.OPTIMAL:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1:
                        esol[event_id]=(period_id,room_id)
            return esol
        elif solver_type=='cplex':
            model=cpx.CpoModel()
            xvars={(event_id,room_id,period_id):model.binary_var(name=f'combination_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in periods}

            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id in problem.event_rooms[event_id]: continue
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)] for period_id in periods
                        ])==0
                    )
                
                for period_id in periods:
                    if period_id in problem.event_periods[event_id]: continue
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)
                        ])==0
                    )
            
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in periods
                    ])==1
                )
            
            for room_id in range(problem.R):
                for period_id in periods:
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                    )
            
            for event_id in eset: 
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in periods:
                        if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)
                            ])<=1
                        )
            
            if problem.formulation=="full":
                for event_id in eset:
                    for event_id2 in problem.after_events[event_id]:
                        if event_id2 in eset:
                            model.add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods 
                                ])
                                <
                                sum([
                                    xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods
                                ])
                            )
            
            single_events={(student_events,day):model.binary_var(name=f'single_events_{student_events}_{day}') for student_events in partial_identical_students.keys() for day in days}
            combination_vars={ecombination:model.binary_var(name=f'ecombination_{ecombination}') for ecombination in ecombinations}

            for student_events in partial_identical_students.keys():
                for day in days:
                    
                    cpx.if_then(
                        single_events[(student_events,day)],sum([
                            xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in range(problem.R) for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)
                        ])==1
                    )

                    cpx.if_then(
                        single_events[(student_events,day)]==1, sum([
                            xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in range(problem.R) for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)
                        ])==0
                    )
            
            for ecombination in ecombinations:
                for day in days:
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                         model.add(
                            sum([
                                xvars[(event_id,room_id,pcurr)]
                                for event_id in ecombination
                                for room_id in range(problem.R)
                                for pcurr in range(period_id,period_id+3)
                            ])<=2+combination_vars[ecombination]
                        )
            
            last_periods_per_day=[day*Core.periods_per_day+Core.periods_per_day-1 for day in days]
            objective=[
                sum([single_events[(student_events,day)] * partial_identical_students[student_events] for student_events in partial_identical_students.keys() for day in days]),
                sum([combination_vars[(ecombination)] * ecombinations[ecombination] for ecombination in ecombinations]),
                sum([xvars[(event_id,room_id,period_id)]*len(problem.events[(event_id,room_id,period_id)]) for event_id in eset for room_id in range(problem.R) for period_id in last_periods_per_day])
            ]

            model.minimize(sum(objective))
            params=cpx.CpoParameters()
            params.TimeLimit=time_limit
            params.Workers=os.cpu_count()
            params.LogVerbosity=True
            model.minimize(params=params)
            solver=model.solve(params=params)
            esol={}

            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1: 
                        esol[event_id]=(period_id,room_id)

            return esol

        elif solver_type=='gurobi':
            try:
                model=gp.Model("Days combined model")
                xvars=model.addVars([(event_id,room_id,period_id) for event_id in eset for room_id in range(problem.R) for period_id in periods],vtype=gp.GRB.BINARY)
                
                if initial_solution:
                    for event_id,(period_id,room_id) in initial_solution.items():
                        model.VarHintVal(xvars[(event_id,room_id,period_id)],1)
                
                for event_id in eset:
                    for room_id in range(problem.R):
                        if room_id in problem.event_rooms[event_id]: continue
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                        )
                    
                    for period_id in periods:
                        if period_id in problem.event_periods[event_id]: continue
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0
                        )
                
                for event_id in eset:
                    model.addConstr(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in periods])==1
                    )
                
                for room_id in range(problem.R):
                    for period_id in periods:
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                        )
                
                for event_id in eset:
                    for event_id2 in problem.G.neighbors(event_id):
                        for period_id in periods:
                            if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                            model.addConstr(
                                sum([xvars[(event_id,room_id,period_id)]*periods for room_id in range(problem.R) for period_id in periods])
                                +sum([xvars[(event_id2,room_id,period_id)] for room_id in range(problem.R) for period_id in periods])
                            )
                if problem.formulation=='full':
                    for event_id in eset:
                        for event_id2 in problem.after_events[event_id]:
                            if event_id2 in eset:
                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                    <sum([xvars[(event_id2,room_id,period_id)] for room_id in range(problem.R) for period_id in periods])
                                )
                            else:
                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])!=initial_solution[event_id2][0]
                                )
                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                    <=initial_solution[event_id2][0]
                                )


                single_events=model.addVars([(student_events,day) for student_events in partial_identical_students.keys() for day in days],vtype=gp.GRB.BINARY)
                combination_vars=model.addVars(ecombinations,vtype=gp.GRB.BINARY)

                for student_events in partial_identical_students.keys():
                    for day in days:
                        model.addConstr(
                            single_events[(student_events,day)]>>sum([xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in range(problem.R) for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)])==1
                        )

                        model.addConstr(
                            single_events[(student_events,day)]==0>>sum([xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in range(problem.R) for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)])!=1
                        )
                
                for ecombination in ecombinations:
                    for day in days:
                        for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                            model.addConstr(
                                sum([xvars[(event_id,room_id,pcurr)] for event_id in ecombination for room_id in range(problem.R) for pcurr in range(period_id,period_id+3)])
                                <=2+combination_vars[ecombination]
                            ) 
                last_periods_of_days=[day*Core.periods_per_day+Core.periods_per_day-1 for day in days]           
                objective=[
                    sum([single_events[(student_events,day)]*partial_identical_students[student_events] for student_events in partial_identical_students.keys() for day in days]),
                    sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations]),
                    sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R) for period_id in last_periods_of_days])
                ]

                model.setObjective(sum(objective),gp.GRB.MINIMIZE)
                model.optimize()


                esol={}
                for (event_id,room_id,period_id),v in xvars.items():
                    if v.X==1: 
                        esol[event_id]=(period_id,room_id)
                return esol

            except gp.GurobiError as e:
                print('Error code ' + str(e.errno) + ': ' + str(e))

            except AttributeError:
                print('Encountered an attribute error')

    @staticmethod
    def preprocessing(solution,init_sol='best',time_limit=600):
        if init_sol=='best':
            solution.read_best()
        elif init_sol=='pool':
            all_solutions=os.listdir(Core.path_to_solutions)
            for solution_name in all_solutions:
                if solution_name.startswith(solution.solution_id):
                    with open(os.path.join(Core.path_to_solutions,solution_name)) as RF:
                        for i,line in enumerate(RF):
                            period_id,room_id=[int(x.strip()) for x in line.split()]
                            if i in solution.events_solution:
                                solution.unschedule(i)
                            solution.schedule(i,period_id,room_id,init=i not in solution.events_solution)
                    break
        else:
            esol=Mathematical_Solver.generate_solution(solution.problem,solver_type='cpsat',time_limit=time_limit)
            new_time_bound=time_limit
            while esol=={}:
                new_time_bound+=300
                esol=Mathematical_Solver.generate_solution(solution.problem,solver_type='cpsat',init=True,time_limit=new_time_bound)
            solution.set_(esol,init=True)
            solution.pickle_sol()
        
        # Day by day optimizer
        initial_cost=solution.compute_cost()
        for day in range(Core.days):
            print(f'SA| Day:{day}\t Cost:{solution.compute_day_cost(day)}/{initial_cost}')
            eset=[event_id for event_id,(period_id,_) in solution.events_solution.items() if period_id//Core.periods_per_day==day]
            partial_solution={event_id:solution.events_solution[event_id] for event_id in eset}
            esol=Mathematical_Solver.day_by_day(solution.problem,eset=eset,day=day,initial_solution=partial_solution,time_limit=40,solver_type='cpsat')
            if esol!={}: 
                solution.set_(esol)
        
def simulated_annealing(solution:Solution,config):
    logger=logging.getLogger('simulated_annealing_temperature')
    logger.setLevel(logging.INFO)
    formatter=logging.Formatter('%(asctime)s\t%(message)s')
    fh=logging.FileHandler(filename=os.path.join('','loggers','post_logger.log'))
    sh=logging.StreamHandler()
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)

    Mathematical_Solver.preprocessing(solution,config.initial_solution,config.init_time_limit)

    if len(solution.events_solution)==0: return
    
    temperature,start_temperature=1000,1000
    alpha=0.9999
    freeze_temperature=1.0
    best_cost=solution.compute_cost()
    best_solution=solution.events_solution
    last_improvement_counter=0
    devide_limit=300000
    timer=time()    
    print(f'{"="*10} Simulated Annealing {"="*10}')
    logger.info(f'SA| Initiating simulated annealing procedure: Cost:{best_cost}')

    while True:
        if solution.compute_cost()==0:
            break
        moves,move_name=solution.get_move()
        if len(moves)==0: 
            if time()-timer>config.solver_time_limit:
                break
            continue
        
        memory={event_id:solution.events_solution[event_id] for event_id in moves}
        current_solution_cost=solution.compute_cost()
        solution.reposition(moves)
        candicate_solution_cost=solution.compute_cost()

        if candicate_solution_cost<best_cost:
            best_solution=solution.events_solution.copy()
            best_cost=candicate_solution_cost
            logger.info(f'SA| New best solution found\tMove:{move_name}\tCost:{candicate_solution_cost}\tT:{temperature}')
            last_improvement_counter=0
            continue
        elif candicate_solution_cost>best_cost:
            last_improvement_counter+=1
            if random.random()<math.exp(-(candicate_solution_cost-current_solution_cost)/temperature):
                logger.debug(f'SA| Higher cost solution accepted\tCost:{candicate_solution_cost}\tT:{temperature}')
            else:
                solution.reposition(memory)
        else:
            last_improvement_counter+=1

        temperature*=alpha

        if last_improvement_counter%devide_limit==0: 
            if time()-timer>config.solver_time_limit:
                logger.info(f'SA| Solution search procedure ended after {time()-timer}\'s\tCost:{best_cost}')
                break
            
            day=random.randint(0,4)
            eset=[event_id for event_id,(period_id,_) in solution.events_solution.items() if period_id//Core.periods_per_day==day]
            partial_solution={event_id:solution.events_solution[event_id] for event_id in eset}
            esol=Mathematical_Solver.day_by_day(solution.problem,eset,day,partial_solution,time_limit=config.day_by_day_time_limit)
            if esol!={}:
                solution.set_(esol)
                best_cost=solution.compute_cost()
                best_solution=solution.events_solution

        if time()-timer>config.solver_time_limit:
            logger.info(f'SA| Solution search procedure ended after {time()-timer}\'s\tCost:{best_cost}')
            break
    
        if temperature<freeze_temperature:
            days=[]
            for _ in range(2):
                day=random.randint(0,4)
                while day in days:
                    day=random.randint(0,4)
                days.append(day)
            temperature=start_temperature*random.uniform(0.5,1.5)
            logger.info(f'Random days selected:{days}\tT={temperature}\tDays={days}')
            eset=[event_id for event_id,(period_id,_) in solution.events_solution.items() if period_id//Core.periods_per_day in days]
            esol=Mathematical_Solver.days_combined_solver(solution.problem,eset,days,solution.events_solution,solver_type=config.solver,time_limit=config.days_combined_time_limit)
            if esol!={}:
                solution.set_(esol)
                best_cost=solution.compute_cost()
                best_solution=solution.events_solution
    
    logger.info(f'SA| After {config.solver_time_limit} \'s the best cost:{best_cost}')
    solution.set_(best_solution)
    solution.feasibility()
    solution.save()

def hill_climbing(solution:Solution,time_limit=600):
    logger=logging.getLogger('hill climbing logger')
    logger.setLevel(logging.INFO)
    formatter=logging.Formatter('%(asctime)s\t%(message)s')
    fh=logging.FileHandler(filename=os.path.join('','loggers','post_logger.log'))
    sh=logging.StreamHandler()
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)

    last_imrovement_counter=0
    last_improvement_threshold=500000
    start_timer=time()

    while True:
        moves,move_name=solution.get_move()
        memory={event_id:solution.events_solution[event_id] for event_id in moves}
        last_improvement_counter=0
        if len(moves)==0: 
            if time()-start_timer>time_limit:
                break
            continue
        
        previous_cost=solution.compute_cost()
        solution.reposition(moves)
        candicate_solution_cost=solution.compute_cost()

        if candicate_solution_cost<previous_cost:
            logger.info(f"HC| New solution found\tCost:{candicate_solution_cost}")
            last_improvement_counter=0
        else:
            solution.reposition(memory)
            last_improvement_counter+=1
        
        if last_improvement_counter%last_improvement_threshold==0:
            pass

import logging,os,random,math
import pickle
import gurobipy as gp
import docplex.cp.model as cpx
from time import time
from base import Problem,Core,Configuration
from ortools.sat.python import cp_model
from itertools import combinations
from ps_solution import Solution

class Mathematical_Solver:
    @staticmethod
    def generate_solution(problem:Problem,verbose=False,time_limit=600,solver_type='cpsat'):
        if solver_type == 'cpsat':
            model=cp_model.CpModel()
            dparams={(event_id,room_id,period_id):model.NewBoolVar(name=f'decision_var_{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(Core.P)}

            # Disable all the unavailability variables
            for event_id in range(problem.E):
                for room_id in range(problem.R):
                    if room_id in problem.event_rooms[event_id]: continue 
                    model.Add(sum([dparams[(event_id,room_id,period_id)] for period_id in range(Core.P)])==0)
                for period_id in range(Core.P):
                    if period_id in problem.event_periods[event_id]:  continue
                    model.Add(sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0)
            
            for event_id in range(problem.E):
                model.Add(sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])==1)
            
            for room_id in range(problem.R):
                for period_id in range(Core.P):
                    model.Add(
                        sum([dparams[(event_id,room_id,period_id)] for event_id in range(problem.E)])<=1
                    )

            for event_id in range(problem.E):
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in range(Core.P):
                        if period_id  not in problem.event_periods[event_id] or period_id  not in problem.event_periods[event_id2]: continue
                        model.Add(
                            sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R)])
                            +sum([dparams[(event_id2,room_id,period_id)] for room_id in range(problem.R)])
                            <=1
                        )
            
            if problem.formulation=='full':
                for event_id in range(problem.E):
                    for event_id2 in problem.after_events[event_id]:
                        model.Add(
                            sum([dparams[(event_id,room_id,period_id)] for room_id in problem.rooms for period_id in range(Core.P)])
                            <sum([dparams[(event_id2,room_id,period_id)] for room_id in problem.rooms for period_id in range(Core.P)]) 
                        )
            
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=time_limit
            solver.parameters.num_search_workers = os.cpu_count()
            solver.parameters.log_search_progress=verbose
            status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
            esol={}
            if status==cp_model.FEASIBLE or status==cp_model.OPTIMAL:
                for (event_id,room_id,period_id),dvar in dparams.items():
                    if solver.Value(dvar)==1:
                        esol[event_id]=(period_id,room_id)
            return esol
        
        elif solver_type=='cplex':
            model=cpx.CpoModel()
            xvars={(event_id,room_id,period_id):model.binary_var(name=f'ecombination_{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}

            for event_id in range(problem.E):
                for room_id in range(problem.R):
                    if room_id in problem.event_rooms[event_id]: continue
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for period_id in range(Core.P)])==0
                    )
                
                for period_id in range(Problem.P):
                    if period_id in problem.event_periods[event_id]: continue
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0
                    )
                
            for event_id in range(Problem.E):
                model.add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])==1
                )
            
            for room_id in range(problem.R):
                for period_id in range(problem.P):
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in range(problem.E)])<=1
                    )
            
            for event_id in range(problem.E):
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in range(Core.P):
                        if period_id in problem.event_periods[event_id] or period_id in problem.event_periods[event_id]: continue
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)                                
                            ])
                            +sum([
                                xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)
                            ])
                            <=1
                        ) 
            
            if problem.formulation=="full":
                for event_id in range(problem.E):
                    for event_id2 in problem.after_events[event_id]:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(Core.P)
                            ])
                            <sum([
                                xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(Core.P)
                            ])
                        )
            
            params=cpx.CpoParameters()
            params.TimeLimit=time_limit
            params.Workers=os.cpu_count()
            params.LogVerbosity=True

            solver=model.solve(params=params)
            esol={}
            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1: 
                        esol[event_id]=(period_id,room_id)
            return esol

        elif solver_type=='gurobi':
            model=gp.Model("mip_model")
            dparams=model.addVars([(event_id,room_id,period_id) for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(Core.P)],vtype=gp.GRB.BINARY)

            # Disable all the unavailability variables
            for event_id in range(problem.E):
                for room_id in range(problem.R):
                    if room_id in problem.event_rooms[event_id]: continue 
                    model.addConstr(sum([dparams[(event_id,room_id,period_id)] for period_id in range(Core.P)])==0)
                for period_id in range(Core.P):
                    if period_id in problem.event_periods[event_id]:  continue
                    model.addConstr(sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0)
            
            for event_id in range(problem.E):
                model.addConstr(sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])==1)
            
            for room_id in range(problem.R):
                for period_id in range(Core.P):
                    model.addConstr(
                        sum([dparams[(event_id,room_id,period_id)] for event_id in range(problem.E)])<=1
                    )

            for event_id in range(problem.E):
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in range(Core.P):
                        if period_id  not in problem.event_periods[event_id] or period_id  not in problem.event_periods[event_id2]: continue
                        model.addConstr(
                            sum([dparams[(event_id,room_id,period_id)] for room_id in range(problem.R)])
                            +sum([dparams[(event_id2,room_id,period_id)] for room_id in range(problem.R)])
                            <=1
                        )
            
            if problem.formulation=='full':
                for event_id in range(problem.E):
                    for event_id2 in problem.after_events[event_id]:
                        x=model.addVar(vtype=gp.GRB.BINARY)
                        model.addConstr(
                            sum([dparams[(event_id,room_id,period_id)]*period_id for room_id in problem.rooms for period_id in range(Core.P)])
                            <=sum([dparams[(event_id2,room_id,period_id)]*period_id for room_id in problem.rooms for period_id in range(Core.P)]) 
                        )
            
            model.optimize()
            
            esol={}
            for (event_id,room_id,period_id),dvar in dparams.items():
                if dvar.X==1:
                    esol[event_id]=(period_id,room_id)
            return esol

    @staticmethod
    def day_by_day(problem:Problem,eset=[],day=0,initial_solution=None,solver_type='cpsat',time_limit=80):
        periods=list(range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day))
        if solver_type=='cpsat':
            model=cp_model.CpModel()
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'decision_variable_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in problem.rooms for period_id in periods}

            if initial_solution: 
                for event_id,(period_id,room_id) in initial_solution.items():
                    model.AddHint(xvars[(event_id,room_id,period_id)],1)

            for event_id in eset:
                for room_id in problem.rooms.keys():
                    if room_id in problem.event_rooms[event_id]: continue 
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                    )

                for period_id in periods:
                    if period_id in problem.event_periods[event_id]: continue
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])==0
                    )
                
            
            for event_id in eset:
                model.Add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys() for period_id in periods])==1
                )
            
            for room_id in problem.rooms.keys():
                for period_id in periods:
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                    )      
            
            for event_id in eset: 
                for event_id2 in list(problem.G.neighbors(event_id)):
                    if event_id2 not in eset: continue
                    for period_id in periods:
                        if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])
                            +sum([xvars[(event_id2,room_id,period_id)] for room_id in problem.rooms.keys()])
                            <=1
                        )
            
            if problem.formulation=='full':
                for event_id in eset:
                    for event_id2 in problem.after_events[event_id]:
                        if event_id2 not in eset: continue
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])
                            <sum([xvars[(event_id2,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])
                        )
            
            ecombinations={frozenset(x):problem.event_combinations[frozenset(x)] for x in combinations(eset,3) if frozenset(x) in problem.event_combinations}
            combination_vars={ecombination:model.NewBoolVar(name=f'event_combinations_{ecombination}') for ecombination in ecombinations}
            for ecombination in ecombinations:
                for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                    model.Add(
                        sum([xvars[(event_id,room_id,current_period)] for event_id in ecombination for room_id in problem.rooms.keys() for current_period in range(period_id,period_id+3)])
                        <=2+combination_vars[ecombination]
                    )

            last_period_of_day=day*Core.periods_per_day+Core.periods_per_day-1
            objective=[
                sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations]),
                sum([len(problem.events[event_id]['S'])*xvars[(event_id,room_id,last_period_of_day)] for event_id in eset for room_id in problem.rooms.keys()])
            ]

            model.Minimize(sum(objective))
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = time_limit
            solver.parameters.num_search_workers = os.cpu_count()
            status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
            esol={}
            if status==cp_model.OPTIMAL or status==cp_model.FEASIBLE:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1: 
                        esol[event_id]=(period_id,room_id)
            return esol

        elif solver_type=='cplex':
            model=cpx.CpoModel()
            xvars={(event_id,room_id,period_id):model.binary_var(name=f'{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in problem.rooms for period_id in periods}

            if initial_solution:
                stp=model.create_empty_solution()
                for event_id in eset:
                    stp[event_id]=initial_solution[event_id]
                model.set_starting_point(stp)

            for event_id in eset:
                for room_id in problem.rooms:
                    if room_id not in problem.event_rooms[event_id]: 
                        model.add(
                            sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                        )

                for period_id in periods:
                    if period_id in problem.event_periods[event_id]:
                        model.add(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])==0
                        )
                
            
            for event_id in eset:
                model.add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys() for period_id in periods])==1
                )
            
            for room_id in problem.rooms.keys():
                for period_id in periods:
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                    )   
            
            for event_id in eset: 
                for event_id2 in problem.G.neighbors(event_id):
                    if event_id2 not in eset: continue
                    for period_id in periods:
                        if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                        model.add(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])
                            +sum([xvars[(event_id2,room_id,period_id)] for room_id in problem.rooms.keys()])
                            <=1
                        )
            
            if problem.formulation=='full':
                for event_id in eset:
                    for event_id2 in problem.after_events[event_id]:
                        if event_id2 not in eset: continue
                        model.add(
                            sum([xvars[(event_id,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])
                            <sum([xvars[(event_id2,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])
                        )
            
            ecombinations={frozenset(x):problem.event_combinations[frozenset(x)] for x in combinations(eset,3) if frozenset(x) in problem.event_combinations}
            combination_vars={ecombination:model.binary_var(name=f'event_combinations_{ecombination}') for ecombination in ecombinations}
            for ecombination in ecombinations:
                for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                    model.add(
                        sum([xvars[(event_id,room_id,current_period)] for event_id in ecombination for room_id in problem.rooms.keys() for current_period in range(period_id,period_id+3)])
                        <=2+combination_vars[ecombination]
                    )
            last_period_of_day=day*Core.periods_per_day+Core.periods_per_day-1
            objective=[
                sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations])
                +sum([len(problem.events[event_id]['S'])*xvars[(event_id,room_id,last_period_of_day)] for event_id in eset for room_id in problem.rooms.keys()])
            ]

            model.minimize(sum(objective))
            params=cpx.CpoParameters()
            params.TimeLimit=time_limit
            params.Workers=os.cpu_count()
            solver=model.solve(params=params)
            esol={}
            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1: 
                        esol[event_id]=(period_id,room_id)
            return esol
        elif solver_type=='gurobi':
            try:
                model=gp.Model("mip_solver_day_by_day")
                xvars=model.addVars([(event_id,room_id,period_id) for event_id in eset for room_id in range(problem.R) for period_id in periods],vtype=gp.GRB.BINARY)
                
                if initial_solution:
                    for event_id,(period_id,room_id) in initial_solution.items():
                        model.VarHintVal(xvars[(event_id,room_id,period_id)],1)

                for event_id in range(problem.E):
                    for room_id in range(problem.R):
                        if room_id in problem.event_rooms[event_id]: continue
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                        )
                    
                    for period_id in periods:
                        if period_id in problem.event_periods[event_id]: continue
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0
                        )
                    
                for event_id in eset:
                    model.addConstr(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in periods])==1
                    )

                for room_id in range(problem.R):
                    for period_id in periods:
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                        )
                
                for event_id in eset:
                    for event_id2 in problem.G.neighbors(event_id):
                        if event_id2 not in eset: continue
                        for period_id in periods:
                            if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                            model.addConstr(
                                sum([xvars[(event_id,room_id,period_id)] for event_id in eset for room_id in range(problem.R)])
                                +sum([xvars[(event_id,room_id,period_id)] for event_id in eset for room_id in range(problem.R)])
                                <=1
                            )
                
                if problem.formulation=="full":
                    for event_id in eset:
                        for event_id2 in problem.after_events[event_id]:
                            if event_id2 not in eset:
                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                    <=sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                )

                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])!=sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                )


                ecombinations={frozenset(x):problem.event_combinations[frozenset(x)] for x in combinations(eset,3) if frozenset(x) in problem.event_combinations}
                combination_vars=model.addVars(ecombinations,vtype=gp.GRB.BINARY)
                for ecombination in ecombinations:
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                        model.addConstr(
                            sum([xvars[(event_id,room_id,current_period)] for event_id in ecombination for room_id in problem.rooms.keys() for current_period in range(period_id,period_id+3)])
                            <=2+combination_vars[ecombination]
                        )
                last_period_of_day=day*Core.periods_per_day+Core.periods_per_day-1
                objective=[
                    sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations]),
                    sum([len(problem.events[event_id]['S'])*xvars[(event_id,room_id,last_period_of_day)] for event_id in eset for room_id in problem.rooms.keys()])
                ]

                model.setObjective(sum(objective),gp.GRB.MINIMIZE)
                model.optimize()

                esol={}
                for (event_id,room_id,period_id),v in xvars.items():
                    if v.X==1: 
                        esol[event_id]=(period_id,room_id)
                return esol
                


            except gp.GurobiError as e:
                print('Error code ' + str(e.errno) + ': ' + str(e))

            except AttributeError:
                print('Encountered an attribute error') 

    @staticmethod
    def days_combined_solver(problem:Problem,eset=[],days=[],initial_solution=None,time_limit=600,solver_type='cpsat'):
        periods=[period_id for day in days for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)]
        ecombinations={frozenset(x):problem.event_combinations[frozenset(x)] for x in combinations(eset,3) if frozenset(x) in problem.event_combinations}
        symmetrical_event_difference=set(problem.events)-set(eset)
        partial_identical_students=dict()
        for events in problem.students.values():
            student_events=set(events)-symmetrical_event_difference
            partial_identical_students[frozenset(student_events)]=partial_identical_students.get(frozenset(student_events),0)+1


        if solver_type=='cpsat':
            model=cp_model.CpModel()
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in problem.rooms.keys() for period_id in periods}

            if initial_solution:
                for event_id in eset:
                    model.AddHint(xvars[(event_id,initial_solution[event_id][1],initial_solution[event_id][0])],1)

            for event_id in eset:
                for room_id in problem.rooms.keys():
                    if room_id in problem.event_rooms[event_id]: continue
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                    )
                
                for period_id in periods:
                    if period_id in problem.event_periods[event_id]: continue
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys()])==0
                    )
            
            for event_id in eset:
                model.Add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in problem.rooms.keys() for period_id in periods])==1
                )
            
            for room_id in problem.rooms.keys():
                for period_id in periods:
                    model.Add(
                        sum([xvars[event_id,room_id,period_id] for event_id in eset])<=1
                    )
            
            for event_id in eset:
                for event_id2 in problem.after_events[event_id]:
                    if event_id2 in eset:
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in problem.rooms.keys() for period_id in periods])
                            <sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in problem.rooms.keys() for period_id in periods])
                        )
                    else:
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)] * period_id for room_id in problem.rooms.keys() for period_id in periods])<initial_solution[event_id2][0]
                        )
            

            single_events={(student_events,day):model.NewBoolVar(name=f'event_set_{student_events}_day_{day}') for student_events in partial_identical_students for day in days}
            combination_vars={ecombination:model.NewBoolVar(name=f'combination_{ecombination}') for ecombination in ecombinations}

            # Single day events
            for student_events in partial_identical_students:
                for day in days:
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in problem.rooms.keys() for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)])==1
                    ).OnlyEnforceIf(single_events[(student_events,day)])

                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in problem.rooms.keys() for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)])!=1
                    ).OnlyEnforceIf(single_events[(student_events,day)].Not())

            # Consecutive events
            for ecombination in ecombinations:
                for day in days:
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                        model.Add(
                            sum([xvars[(event_id,room_id,pcurr)] for event_id in ecombination for room_id in problem.rooms.keys() for pcurr in range(period_id,period_id+3)])
                            <=2+combination_vars[ecombination]
                        )
            
            last_periods_of_days=[day*Core.periods_per_day+Core.periods_per_day-1 for day in days]

            objective=[
                sum([single_events[(student_events,day)]*partial_identical_students[student_events] for student_events in list(partial_identical_students.keys()) for day in days]),
                sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations]),
                sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in eset for room_id in problem.rooms.keys() for period_id in last_periods_of_days])
            ]

            model.Minimize(sum(objective))
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=time_limit
            solver.parameters.num_search_workers=os.cpu_count()
            solver.parameters.log_search_progress=True
            status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
            esol={}
            if status==cp_model.FEASIBLE or status==cp_model.OPTIMAL:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1:
                        esol[event_id]=(period_id,room_id)
            return esol
        elif solver_type=='cplex':
            model=cpx.CpoModel()
            xvars={(event_id,room_id,period_id):model.binary_var(name=f'combination_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in periods}

            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id in problem.event_rooms[event_id]: continue
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)] for period_id in periods
                        ])==0
                    )
                
                for period_id in periods:
                    if period_id in problem.event_periods[event_id]: continue
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)
                        ])==0
                    )
            
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in periods
                    ])==1
                )
            
            for room_id in range(problem.R):
                for period_id in periods:
                    model.add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                    )
            
            for event_id in eset: 
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in periods:
                        if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)
                            ])<=1
                        )
            
            if problem.formulation=="full":
                for event_id in eset:
                    for event_id2 in problem.after_events[event_id]:
                        if event_id2 in eset:
                            model.add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods 
                                ])
                                <
                                sum([
                                    xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods
                                ])
                            )
            
            single_events={(student_events,day):model.binary_var(name=f'single_events_{student_events}_{day}') for student_events in partial_identical_students.keys() for day in days}
            combination_vars={ecombination:model.binary_var(name=f'ecombination_{ecombination}') for ecombination in ecombinations}

            for student_events in partial_identical_students.keys():
                for day in days:
                    
                    cpx.if_then(
                        single_events[(student_events,day)],sum([
                            xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in range(problem.R) for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)
                        ])==1
                    )

                    cpx.if_then(
                        single_events[(student_events,day)]==1, sum([
                            xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in range(problem.R) for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)
                        ])==0
                    )
            
            for ecombination in ecombinations:
                for day in days:
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                         model.add(
                            sum([
                                xvars[(event_id,room_id,pcurr)]
                                for event_id in ecombination
                                for room_id in range(problem.R)
                                for pcurr in range(period_id,period_id+3)
                            ])<=2+combination_vars[ecombination]
                        )
            
            last_periods_per_day=[day*Core.periods_per_day+Core.periods_per_day-1 for day in days]
            objective=[
                sum([single_events[(student_events,day)] * partial_identical_students[student_events] for student_events in partial_identical_students.keys() for day in days]),
                sum([combination_vars[(ecombination)] * ecombinations[ecombination] for ecombination in ecombinations]),
                sum([xvars[(event_id,room_id,period_id)]*len(problem.events[(event_id,room_id,period_id)]) for event_id in eset for room_id in range(problem.R) for period_id in last_periods_per_day])
            ]

            model.minimize(sum(objective))
            params=cpx.CpoParameters()
            params.TimeLimit=time_limit
            params.Workers=os.cpu_count()
            params.LogVerbosity=True
            model.minimize(params=params)
            solver=model.solve(params=params)
            esol={}

            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1: 
                        esol[event_id]=(period_id,room_id)

            return esol

        elif solver_type=='gurobi':
            try:
                model=gp.Model("Days combined model")
                xvars=model.addVars([(event_id,room_id,period_id) for event_id in eset for room_id in range(problem.R) for period_id in periods],vtype=gp.GRB.BINARY)
                
                if initial_solution:
                    for event_id,(period_id,room_id) in initial_solution.items():
                        model.VarHintVal(xvars[(event_id,room_id,period_id)],1)
                
                for event_id in eset:
                    for room_id in range(problem.R):
                        if room_id in problem.event_rooms[event_id]: continue
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for period_id in periods])==0
                        )
                    
                    for period_id in periods:
                        if period_id in problem.event_periods[event_id]: continue
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0
                        )
                
                for event_id in eset:
                    model.addConstr(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in periods])==1
                    )
                
                for room_id in range(problem.R):
                    for period_id in periods:
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)] for event_id in eset])<=1
                        )
                
                for event_id in eset:
                    for event_id2 in problem.G.neighbors(event_id):
                        for period_id in periods:
                            if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                            model.addConstr(
                                sum([xvars[(event_id,room_id,period_id)]*periods for room_id in range(problem.R) for period_id in periods])
                                +sum([xvars[(event_id2,room_id,period_id)] for room_id in range(problem.R) for period_id in periods])
                            )
                if problem.formulation=='full':
                    for event_id in eset:
                        for event_id2 in problem.after_events[event_id]:
                            if event_id2 in eset:
                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                    <sum([xvars[(event_id2,room_id,period_id)] for room_id in range(problem.R) for period_id in periods])
                                )
                            else:
                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])!=initial_solution[event_id2][0]
                                )
                                model.addConstr(
                                    sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in periods])
                                    <=initial_solution[event_id2][0]
                                )


                single_events=model.addVars([(student_events,day) for student_events in partial_identical_students.keys() for day in days],vtype=gp.GRB.BINARY)
                combination_vars=model.addVars(ecombinations,vtype=gp.GRB.BINARY)

                for student_events in partial_identical_students.keys():
                    for day in days:
                        model.addConstr(
                            single_events[(student_events,day)]>>sum([xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in range(problem.R) for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)])==1
                        )

                        model.addConstr(
                            single_events[(student_events,day)]==0>>sum([xvars[(event_id,room_id,period_id)] for event_id in student_events for room_id in range(problem.R) for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day)])!=1
                        )
                
                for ecombination in ecombinations:
                    for day in days:
                        for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-3):
                            model.addConstr(
                                sum([xvars[(event_id,room_id,pcurr)] for event_id in ecombination for room_id in range(problem.R) for pcurr in range(period_id,period_id+3)])
                                <=2+combination_vars[ecombination]
                            ) 
                last_periods_of_days=[day*Core.periods_per_day+Core.periods_per_day-1 for day in days]           
                objective=[
                    sum([single_events[(student_events,day)]*partial_identical_students[student_events] for student_events in partial_identical_students.keys() for day in days]),
                    sum([combination_vars[ecombination]*ecombinations[ecombination] for ecombination in ecombinations]),
                    sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R) for period_id in last_periods_of_days])
                ]

                model.setObjective(sum(objective),gp.GRB.MINIMIZE)
                model.optimize()


                esol={}
                for (event_id,room_id,period_id),v in xvars.items():
                    if v.X==1: 
                        esol[event_id]=(period_id,room_id)
                return esol

            except gp.GurobiError as e:
                print('Error code ' + str(e.errno) + ': ' + str(e))

            except AttributeError:
                print('Encountered an attribute error')

    @staticmethod
    def preprocessing(solution,init_sol='best',time_limit=600):
        if init_sol=='best':
            solution.read_best()
        elif init_sol=='pool':
            all_solutions=os.listdir(Core.path_to_solutions)
            for solution_name in all_solutions:
                if solution_name.startswith(solution.solution_id):
                    with open(os.path.join(Core.path_to_solutions,solution_name)) as RF:
                        for i,line in enumerate(RF):
                            period_id,room_id=[int(x.strip()) for x in line.split()]
                            if i in solution.events_solution:
                                solution.unschedule(i)
                            solution.schedule(i,period_id,room_id,init=i not in solution.events_solution)
                    break
        else:
            esol=Mathematical_Solver.generate_solution(solution.problem,solver_type='cpsat',time_limit=time_limit)
            new_time_bound=time_limit
            while esol=={}:
                new_time_bound+=300
                esol=Mathematical_Solver.generate_solution(solution.problem,solver_type='cpsat',init=True,time_limit=new_time_bound)
            solution.set_(esol,init=True)
            solution.pickle_sol()
        
        # Day by day optimizer
        initial_cost=solution.compute_cost()
        for day in range(Core.days):
            print(f'SA| Day:{day}\t Cost:{solution.compute_day_cost(day)}/{initial_cost}')
            eset=[event_id for event_id,(period_id,_) in solution.events_solution.items() if period_id//Core.periods_per_day==day]
            partial_solution={event_id:solution.events_solution[event_id] for event_id in eset}
            esol=Mathematical_Solver.day_by_day(solution.problem,eset=eset,day=day,initial_solution=partial_solution,time_limit=40,solver_type='cpsat')
            if esol!={}: 
                solution.set_(esol)
        
def simulated_annealing(solution:Solution,config):
    logger=logging.getLogger('simulated_annealing_temperature')
    logger.setLevel(logging.INFO)
    formatter=logging.Formatter('%(asctime)s\t%(message)s')
    fh=logging.FileHandler(filename=os.path.join('','loggers','post_logger.log'))
    sh=logging.StreamHandler()
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)

    Mathematical_Solver.preprocessing(solution,config.initial_solution,config.init_time_limit)

    if len(solution.events_solution)==0: return
    
    temperature,start_temperature=1000,1000
    alpha=0.9999
    freeze_temperature=1.0
    best_cost=solution.compute_cost()
    best_solution=solution.events_solution
    last_improvement_counter=0
    devide_limit=300000
    timer=time()    
    print(f'{"="*10} Simulated Annealing {"="*10}')
    logger.info(f'SA| Initiating simulated annealing procedure: Cost:{best_cost}')

    while True:
        if solution.compute_cost()==0:
            break
        moves,move_name=solution.get_move()
        if len(moves)==0: 
            if time()-timer>config.solver_time_limit:
                break
            continue
        
        memory={event_id:solution.events_solution[event_id] for event_id in moves}
        current_solution_cost=solution.compute_cost()
        solution.reposition(moves)
        candicate_solution_cost=solution.compute_cost()

        if candicate_solution_cost<best_cost:
            best_solution=solution.events_solution.copy()
            best_cost=candicate_solution_cost
            logger.info(f'SA| New best solution found\tMove:{move_name}\tCost:{candicate_solution_cost}\tT:{temperature}')
            last_improvement_counter=0
            continue
        elif candicate_solution_cost>best_cost:
            last_improvement_counter+=1
            if random.random()<math.exp(-(candicate_solution_cost-current_solution_cost)/temperature):
                logger.debug(f'SA| Higher cost solution accepted\tCost:{candicate_solution_cost}\tT:{temperature}')
            else:
                solution.reposition(memory)
        else:
            last_improvement_counter+=1

        temperature*=alpha

        if last_improvement_counter%devide_limit==0: 
            if time()-timer>config.solver_time_limit:
                logger.info(f'SA| Solution search procedure ended after {time()-timer}\'s\tCost:{best_cost}')
                break
            
            day=random.randint(0,4)
            eset=[event_id for event_id,(period_id,_) in solution.events_solution.items() if period_id//Core.periods_per_day==day]
            partial_solution={event_id:solution.events_solution[event_id] for event_id in eset}
            esol=Mathematical_Solver.day_by_day(solution.problem,eset,day,partial_solution,time_limit=config.day_by_day_time_limit)
            if esol!={}:
                solution.set_(esol)
                best_cost=solution.compute_cost()
                best_solution=solution.events_solution

        if time()-timer>config.solver_time_limit:
            logger.info(f'SA| Solution search procedure ended after {time()-timer}\'s\tCost:{best_cost}')
            break
    
        if temperature<freeze_temperature:
            days=[]
            for _ in range(2):
                day=random.randint(0,4)
                while day in days:
                    day=random.randint(0,4)
                days.append(day)
            temperature=start_temperature*random.uniform(0.5,1.5)
            logger.info(f'Random days selected:{days}\tT={temperature}\tDays={days}')
            eset=[event_id for event_id,(period_id,_) in solution.events_solution.items() if period_id//Core.periods_per_day in days]
            esol=Mathematical_Solver.days_combined_solver(solution.problem,eset,days,solution.events_solution,solver_type=config.solver,time_limit=config.days_combined_time_limit)
            if esol!={}:
                solution.set_(esol)
                best_cost=solution.compute_cost()
                best_solution=solution.events_solution
    
    logger.info(f'SA| After {config.solver_time_limit} \'s the best cost:{best_cost}')
    solution.set_(best_solution)
    solution.feasibility()
    solution.save()

def hill_climbing(solution:Solution,time_limit=600):
    logger=logging.getLogger('hill climbing logger')
    logger.setLevel(logging.INFO)
    formatter=logging.Formatter('%(asctime)s\t%(message)s')
    fh=logging.FileHandler(filename=os.path.join('','loggers','post_logger.log'))
    sh=logging.StreamHandler()
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)

    last_imrovement_counter=0
    last_improvement_threshold=500000
    start_timer=time()

    while True:
        moves,move_name=solution.get_move()
        memory={event_id:solution.events_solution[event_id] for event_id in moves}
        last_improvement_counter=0
        if len(moves)==0: 
            if time()-start_timer>time_limit:
                break
            continue
        
        previous_cost=solution.compute_cost()
        solution.reposition(moves)
        candicate_solution_cost=solution.compute_cost()

        if candicate_solution_cost<previous_cost:
            logger.info(f"HC| New solution found\tCost:{candicate_solution_cost}")
            last_improvement_counter=0
        else:
            solution.reposition(memory)
            last_improvement_counter+=1
        
        if last_improvement_counter%last_improvement_threshold==0:
            pass
