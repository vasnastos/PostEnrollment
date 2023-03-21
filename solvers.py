from ortools.sat.python import cp_model
import docplex.cp.model as cpx
from pe import Problem,PRF,Solution
import os,pickle
from itertools import combinations,product
import gurobipy as gp

def create_timetable(problem:"Problem",csolver='cp-sat',save='txt',timesol=600):
    """
        Initial solution creator. It constructs 3 different solutions using 3 different models(cp-sat,cplex-Cp and gurobi-mip)
        Parameters:
            - problem: A problem instance load by class Problem
            - csolver: The type of the solver is used for consructing initial solutions("cp-sat","cp-cplex","gurobi")
            - save: Format that the solution could be potential saved("txt","pickle","None")
            - timesol: time in seconds the the solver would run for
        Returns:
            - dict: contains the generated timetable
    """

    generated_solution={}
    if csolver=='cp-sat':
        model=cp_model.CpModel()
        xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}

        # 1. One event should be placed in only one room in only one period
        for event_id in range(problem.E):
            model.Add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for room_id in range(problem.R)
                    for period_id in range(problem.P)
                ])==1
            )
        
        # 2. Events should not be placed in non valid rooms or periods
        for event_id in range(problem.E):
            for room_id in range(problem.R):
                if room_id not in problem.event_available_rooms[event_id]:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])==0
                    )
            
            for period_id in range(problem.P):
                if period_id not in problem.event_available_periods[event_id]:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])==0
                    )

        # 3. One event should be schedule at each period-room pair
        for room_id in range(problem.R):
            for period_id in range(problem.P):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in range(problem.E)
                    ])<=1
                )


        # 4. Add neighborhood constraints
        for event_id in range(problem.E):
            for neighbor_id in list(problem.G.neighbors(event_id)):
                for period_id in range(problem.P):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])+sum([
                            xvars[(neighbor_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])<=1
                    )

        # 5. Add precedence relations
        if PRF.has_extra_constraints(problem.formulation):
            for event_id in range(problem.E):
                for event_id2 in problem.events[event_id]['HPE']:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])<sum([
                            xvars[(event_id2,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])
                    )
        
        solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds=timesol
        solver.parameters.num_search_workers=os.cpu_count()
        solver.parameters.log_search_progress=True
        status=solver.Solve(model,solution_callback=cp_model.ObjectiveSolutionPrinter)
        if status in [cp_model.FEASIBLE,cp_model.OPTIMAL]:
            for (event_id,room_id,period_id),dvar in xvars.items():
                if solver.Value(dvar)==1:
                    generated_solution[event_id]=(period_id,room_id)
    
    elif  csolver=="cp-cplex":
        # cplex solver
        model=cpx.CpoModel(name='post_enrollment_timetable_constructor')
        xvars={(event_id,room_id,period_id):model.binary_var(name={f"sd_{event_id}_{room_id}_{period_id}"}) for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}

        for event_id in range(problem.E):
            model.add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for room_id in range(problem.R)
                    for period_id in range(problem.P)
                ])==1
            )
        
        # 2. Events should not be placed in non valid rooms or periods
        for event_id in range(problem.E):
            for room_id in range(problem.R):
                if room_id not in problem.event_available_rooms[event_id]:
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])==0
                    )
            
            for period_id in range(problem.P):
                if period_id not in problem.event_available_periods[event_id]:
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])==0
                    )

        # 3. One event should be schedule at each period-room pair
        for room_id in range(problem.R):
            for period_id in range(problem.P):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in range(problem.E)
                    ])<=1
                )


        # 4. Add neighborhood constraints
        for event_id in range(problem.E):
            for neighbor_id in problem.G.neighbors(event_id):
                for period_id in range(problem.P):
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])+sum([
                            xvars[(neighbor_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])<=1
                    )

        
        # 5. Add precedence relations
        if PRF.has_extra_constraints(problem.formulation):
            for event_id in range(problem.E):
                for event_id2 in problem.events[event_id]['HPE']:
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])<sum([
                            xvars[(event_id2,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])
                    )
        params=cpx.CpoParameters()
        params.TimeLimit=timesol
        params.Workers=os.cpu_count()
        
        solver=model.solve(params=params)

        if solver:
            for (event_id,room_id,period_id),dvar in xvars.items():
                if solver[dvar]==1:
                    generated_solution[event_id]=(room_id,period_id)


    elif csolver=='gurobi':
        # Gurobi solver
        model=gp.Model(name="Gurobi_post_enrollment")
        xvars=model.addVars([(event_id,room_id,period_id) for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)],vtype=gp.GRB.BINARY,name='xvars')

        for event_id in range(problem.E):
            model.addConstr(
                xvars.sum(event_id,'*','*')==1,name=f'Constr_{event_id}'
            )
        
        for event_id in range(problem.E):
            for room_id in range(problem.R):
                if room_id not in problem.event_available_rooms[event_id]:
                    model.addConstr(
                        xvars.sum(event_id,room_id,'*')==0
                    )
        
            for period_id in range(problem.P):
                if period_id not in problem.event_available_periods[event_id]:
                    model.addConstr(
                        xvars.sum(event_id,'*',period_id)==0,name=f'Period_Constr_{event_id}'
                    )
        
        for room_id in range(problem.R):
            for period_id in range(problem.P):
                model.addConstr(
                    xvars.sum('*',room_id,period_id)<=1,name=f'room_period_Constr_({room_id},{period_id})'
                )
        
        for event_id in range(problem.E):
            for event_id2 in problem.G.neighbors(event_id):
                for period_id in range(problem.P):
                    model.addConstr(
                        xvars.sum(event_id,'*',period_id)
                        +xvars.sum(event_id2,'*',period_id)<=1
                    )
        if PRF.has_extra_constraints(problem.formulation):
            for event_id in range(problem.E):
                for event_id2 in problem.events[event_id]['HPE']:
                    model.addConstr(
                        sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(problem.P)])<
                        sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(problem.P)])
                    )
        
        model.Params.TimeLimit=timesol
        model.Params.Threads=os.cpu_count()
        model.optimize()

        for (event_id,room_id,period_id),decision_var in xvars.items():
            if decision_var.X==1:
                generated_solution[event_id]=(period_id,room_id)
    
    # save options
    if save=='txt':
        with open(os.path.join('','results','OR-tools',f'{problem.id}.sol'),'w') as writer:
            for event_id,(period_id,room_id) in generated_solution.items():
                writer.write(f'{event_id} {period_id} {room_id}')
    elif save=='pickle':
        with open(os.path.join('','results','OR-tools',f'{problem.id}.pcl_sol'),'wb') as writer:
            pickle.dump(generated_solution,writer)

    return generated_solution


def solve(problem:"Problem",tsolver='cpsat',solution_hint=None,day_by_day=False,days_combined=False,full=False,timesol=600,**kwargs):
    if sum([day_by_day,full,days_combined])==0:
        raise ValueError("Both day_by_day and full params setted to False.\n You should set one of the parameters in True")
    elif sum([day_by_day,full])>1:
        raise ValueError("You set day_by_day and full solver to True. You must select one of the solvers to use")

    generated_solution=dict()

    if tsolver=="cpsat" and full:
        model=cp_model.CpModel()
        xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}

        # Add hint to the solution
        if solution_hint:
            for event_id,(period_id,room_id) in solution_hint.items():
                model.AddHint(xvars[(event_id,room_id,period_id)],1)

        # Constraints
        for event_id in range(problem.E):
            model.Add(
                sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(problem.P)])==1
            )
        
        for event_id in range(problem.E):
            for room_id in range(problem.R):
                if room_id in problem.event_available_rooms[event_id]:
                    continue
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)] for period_id in range(problem.P)
                    ])==0
                )

        for room_id in range(problem.R):
            for period_id in range(problem.P):
                model.Add(
                    sum([xvars[(event_id,room_id,period_id)] for event_id in range(problem.E)])
                    <=1
                )
        
        for event_id in range(problem.E):
            for event_id2 in problem.G.neighbors(event_id):
                for period_id in range(problem.P):
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])
                        +sum([xvars[(event_id2,room_id,period_id)] for room_id in range(problem.R)])
                        <=1
                    )
        
        if PRF.has_extra_constraints(problem.formulation):
            for period_id in range(problem.P):
                if period_id in problem.event_available_periods[event_id]:
                    continue
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)] for event_id in range(problem.E) for room_id in range(problem.R)
                    ])==0
                )

            for event_id in range(problem.E):
                for event_id2 in problem.events[event_id]['HPE']:
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(problem.P)])<
                        sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(problem.P)])
                    )
        
        single_event_days={(student_id,day):model.NewBoolVar(name=f'{student_id}_{day}') for student_id in range(problem.S) for day in range(problem.days)}
        consecutive_events={combination:model.NewBoolVar(name=f'ecombination_{combination}') for combination in problem.event_combinations}

        # Soft constraints 
        # 1. Single event days
        for student_id in range(problem.S):
            for day in range(problem.days):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in range(problem.E)
                        for room_id in range(problem.R)
                        for period_id in range(day * problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                    ])==1
                ).OnlyEnforceIf(single_event_days[(student_id,day)])

                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in range(problem.E)
                        for room_id in range(problem.R)
                        for period_id in range(day * problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                    ])!=1
                ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
        
        # 2. consecutive events
        for ecombination in problem.event_combinations:
            for day in range(problem.days):
                for pcons in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-3):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in ecombination
                            for room_id in range(problem.R)
                            for period_id in range(pcons,pcons+3)
                        ])<=2+consecutive_events[ecombination]
                    )
        
        objective=[
            sum([single_event_days[(student_id,day)] for student_id in range(problem.S) for day in range(problem.days)]),
            sum([consecutive_events[ecombination] * no_students for ecombination,no_students in problem.event_combinations.items()]),
            sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in range(problem.E) for room_id in range(problem.R) for period_id in problem.last_period_per_day])
        ]

        model.Minimize(sum(objective))

        solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds=timesol
        solver.parameters.num_search_workers=os.cpu_count()
        status=solver.Solve(model)
        if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
            for (event_id,room_id,period_id),dvar in xvars.items():
                if solver.Value(dvar)==1:
                    generated_solution[event_id]=(period_id,room_id)
    
    elif day_by_day:
        if 'day' not in kwargs:
            raise ValueError("Day-by-Day solver called and no day provided")
        if 'solution_hint' not in kwargs:
            raise ValueError("No initial solution provided")
        
        day=int(kwargs['day'])
        solution_hint=kwargs['solution_hint']
        eset=[event_id for event_id,(period_id,_) in solution_hint.items() if period_id//problem.periods_per_day==day]
        event_combinations={frozenset(ecombination):problem.event_combinations[frozenset(ecombination)] for ecombination in combinations(eset) if frozenset(ecombination) in problem.event_combinations}


        if tsolver=='cp-sat':
            model=cp_model.CpModel()
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)}

            for event_id in eset:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in range(problem.P)
                    ])==1
                )
            
            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id in problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                            ])==0
                        )
                
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    if period_id not in problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(problem.R)
                            ])==0
                        )


            for room_id in range(problem.R):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in eset
                        ])<=1
                    )
            
            for event_id in eset:
                for neighbor_id in list(problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                ])
                                +sum([
                                    xvars[(neighbor_id,room_id,period_id)]
                                    for room_id in range(problem.R)    
                                ])<=1
                            )
            
            if PRF.has_extra_constraints(problem.formulation):
                for event_id in eset:
                    for event_id2 in problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(problem.P)
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(day*problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                                ])
                            )

            consecutive_events={ecombination:model.NewBoolVar(name=f'{"_".join(list(ecombination))}') for ecombination in event_combinations}

            for ecombination in event_combinations.keys():
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-3):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,pid)]
                            for event_id in ecombination
                            for room_id in range(problem.R)
                            for pid in range(period_id,period_id+3)
                        ])<2+consecutive_events[ecombination]
                    )
            
            objective=[
                sum([consecutive_events[ecombination] * no_students for ecombination,no_students in event_combinations.items()]),
                sum([xvars[(event_id,room_id,day * problem.periods_per_day+problem.periods_per_day-1)] * len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R)])
            ]
            
            model.Minimize(sum(objective))
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=timesol
            solver.parameters.num_search_workers=os.cpu_count()
            solver.parameters.log_search_progress=True
            status=solver.Solve(model=model,solution_callback=cp_model.ObjectiveSolutionPrinter())
            if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1:
                       generated_solution[event_id]=(period_id,room_id)

        elif tsolver=='cplex':
            model=cpx.CpoModel(name='cplex_post_enrollment')
            xvars={(event_id,room_id.period_id):model.binary_var(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)}     

            for event_id in eset:
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in range(problem.P)
                    ])==1
                )
            
            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id in problem.event_available_periods[event_id]:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                            ])==0
                        )
                
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    if period_id not in problem.event_available_periods[event_id]:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(problem.R)
                            ])==0
                        )


            for room_id in range(problem.R):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in eset
                        ])<=1
                    )
            
            for event_id in eset:
                for neighbor_id in list(problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                            model.add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                ])
                                +sum([
                                    xvars[(neighbor_id,room_id,period_id)]
                                    for room_id in range(problem.R)    
                                ])<=1
                            )
            
            if PRF.has_extra_constraints(problem.formulation):
                for event_id in eset:
                    for event_id2 in problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(problem.P)
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(day*problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                                ])
                            )

            consecutive_events={ecombination:model.binary_var(name=f'{"_".join(list(ecombination))}') for ecombination in event_combinations}

            for ecombination in consecutive_events.keys():
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-3):
                    model.add(
                        sum([
                            xvars[(event_id,room_id,pid)]
                            for event_id in ecombination
                            for room_id in range(problem.R)
                            for pid in range(period_id,period_id+3)
                        ])<2+consecutive_events[ecombination]
                    )
            
            objective=[
                sum([consecutive_events[ecombination] * no_students for ecombination,no_students in event_combinations.items()]),
                sum([xvars[(event_id,room_id,day * problem.periods_per_day+problem.periods_per_day-1)] * len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R)])
            ]
            
            model.minimize(sum(objective))
            params=cpx.CpoParameters()
            params.Workers=os.cpu_count()
            params.TimeLimit=timesol
            params.LogVerbosity=True
            solver=model.solve(params=params)
            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1:
                       generated_solution[event_id]=(period_id,room_id)
        
        elif tsolver=='gurobi':
            model=gp.Model()
            xvars=model.addVars(list(product(*[eset,list(range(problem.R)),list(range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day))])),name=f'decision_variables_post',vtype=gp.GRB.BINARY)

            for event_id in eset:
                model.addConstr(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in range(problem.P)
                    ])==1,name=f'EC1_{event_id}'
                )
            
            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id in problem.event_available_periods[event_id]:
                        model.addConstr(
                            xvars.sum(event_id,room_id,'*')==0,name=f'EC2_{event_id}_{room_id}_{period_id}'
                        )
                
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    if period_id not in problem.event_available_periods[event_id]:
                        model.addConstr(
                            xvars.sum(event_id,'*',period_id)==0,name=f'EC3_{period_id}'
                        )


            for room_id in range(problem.R):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    model.addConstr(
                        xvars.sum('*',room_id,period_id)<=1,name=f'EC4_{room_id}_{period_id}'
                    )
            
            for event_id in eset:
                for neighbor_id in list(problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                            model.add(
                                xvars.sum(event_id,'*',period_id)
                                +xvars.sum(neighbor_id,'*',period_id)<=1,name=f'EC5_{event_id}_{neighbor_id}_{period_id}'
                            )
            
            if PRF.has_extra_constraints(problem.formulation):
                for event_id in eset:
                    for event_id2 in problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.addConstr(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(problem.P)
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(day*problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                                ]),name=f'EC6_{event_id}_{event_id2}'
                            )
            
            consecutive_events=model.addVars(list(product(*[eset,list(range(problem.R)),list(range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day))])),name=f'secondary_variables',vtype=gp.GRB.BINARY)
            for ecombination in list(event_combinations.keys()):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-3):
                    model.addConstr(
                        sum([
                            xvars[(event_id,room_id,pid)].V
                            for event_id in list(ecombination)
                            for room_id in range(problem.R)
                            for pid in range(period_id,period_id+3)
                        ])<2+consecutive_events[ecombination]
                    )
            
            objective=[
                sum([consecutive_events[ecombination] * no_students for ecombination,no_students in event_combinations.items()]),
                sum([xvars[(event_id,room_id)] for event_id in eset for room_id in range(problem.R)])
            ]

            model.setObjective(sum(objective))
            model.optimize()

            for (event_id,room_id,period_id),dvar in xvars.items():
                if dvar.X==1:
                    generated_solution[event_id]=(period_id,room_id)
    
    elif days_combined:
        if 'days' not in kwargs:
            raise ValueError("You did not provide the right amount of arguments in the solver")
        days=kwargs['days']
        
        if 'solution_hint' not in kwargs:
            solution_hint=None
        else:
            solution_hint=kwargs['solution_hint']

        if tsolver=='cp-sat':
            model=cp_model.CpModel()
            eset=[event_id for event_id,(period_id,_) in solution_hint.items() if period_id//problem.periods_per_day in days]
            periods=[period_id for day in days for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)]
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in periods}
            partial_student_set=set([student_id for event_id in eset for student_id in problem.events[event_id]['S']])
            shints=problem.create_hints(eset,solution_hint)

            for event_id,(period_id,room_id) in solution_hint.items():
                model.AddHint(xvars[(event_id,room_id,period_id)],1)

            for event_id in eset:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in periods
                    ])==1
                )
            
            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id not in problem.event_available_rooms[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for period_id in periods
                            ])==0
                        )
                for period_id in periods:
                    if period_id not in problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(problem.R)
                            ])==0
                        )
            
            for room_id in range(problem.R):
                for period_id in periods:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in eset
                        ])<=1
                    )

            for event_id in eset:
                for neighbor_id in list(problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in periods:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                ])+sum([
                                    xvars[(neighbor_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                ])<=1
                            )
                    else:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,solution_hint[event_id]['P'])]
                                for room_id in range(problem.R)
                            ])==0
                        )
            
            if PRF.has_extra_constraints(problem.formulation):
                for event_id in eset:
                    for event_id2 in problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]*period_id
                                    for room_id in range(problem.R)
                                    for period_id in periods
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]*period_id
                                    for room_id in range(problem.R)
                                    for period_id in periods
                                ])
                            )
                        else:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]*period_id
                                    for room_id in range(problem.R)
                                    for period_id in periods
                                ])<solution_hint[event_id2]['P']
                            )
            
            single_event_days={(student_id,day):model.NewBoolVar(name=f'se_{student_id}_{day}') for student_id in partial_student_set for day in days}
            consecutive_events={(student_id,day,i):model.NewBoolVar(name=f'se_{student_id}_{day}_{i}') for student_id in partial_student_set for day in days for i in range(3,10)}

            for student_id in partial_student_set:
                student_events_set=[event_id for event_id in problem.students[student_id] if event_id in eset]
                for day in days:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in student_events_set
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])==1
                    ).OnlyEnforceIf(single_event_days[(student_id,day)])

                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in student_events_set
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])!=1
                    ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
                    
                    for i in range(3,10):
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-i+1):
                            if period_id>day*problem.periods_per_day:
                                previous_period_cost=sum([xvars[(event_id,room_id,period_id-1)] for event_id in student_events_set for room_id in range(problem.R)])+shints[student_id][period_id-1]
                            if period_id<day*problem.periods_per_day+problem.periods_per_day-i-1:
                                next_period_cost=sum([xvars[(event_id,room_id,period_id+i)] for event_id in student_events_set for room_id in range(problem.R)])+shints[student_id][period_id]

                            model.Add(
                                previous_period_cost
                                -sum([
                                    xvars[(event_id,room_id,pid)]
                                    for event_id in student_events_set
                                    for room_id in range(problem.R)
                                    for pid in range(period_id,period_id+i)
                                ])-sum([
                                    shints[student_id][pid]
                                    for pid in range(period_id,period_id+i)
                                ])
                                +next_period_cost>=-(i-1)
                            )

            objective=[
                sum([single_event_days[(student_id,day)] for student_id in partial_student_set for day in days]),
                sum([consecutive_events[(student_id,day,i)]*(i-2) for student_id in partial_student_set for day in days for i in range(3,10)]),
                sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R) for period_id in [day*problem.periods_per_day+problem.periods_per_day-1 for day in days]])
            ]

            model.Minimize(sum(objective))
            solver=cp_model.CpSolver()
            solver.parameters.num_search_workers=os.cpu_count()
            solver.parameters.max_time_in_seconds=timesol
            solver.parameters.log_search_progress=True
            status=solver.Solve(model=model,solution_callback=cp_model.ObjectiveSolutionPrinter())
            if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1:
                        generated_solution[event_id]=(period_id,room_id)

    return generated_solution

def timeslot_block_reassignment(problem:Problem,events_in_timeblock:list,frozen_periods:list,solution_hint=None,timesol=60):
    model=cp_model.CpModel()
    xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in events_in_timeblock for room_id in range(problem.R) for period_id in range(problem.P)}
    partial_students_set=set([student_id for event_id in events_in_timeblock for student_id in problem.events[event_id]['S']])

    # 1. Place all events in one exact timeslot
    for event_id in events_in_timeblock:
        model.Add(
            sum([
                xvars[(event_id,room_id,period_id)]
                for room_id in range(problem.R)
                for period_id in range(problem.P)
            ])==1
        )

    # 2. Freeze the periods that are not suitable for the event
    for event_id in events_in_timeblock:
        for room_id in range(problem.R):
            if room_id not in problem.event_available_rooms[event_id]:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for period_id in range(problem.P)
                    ])==0
                )
        
        for period_id in range(problem.P):
            if period_id not in problem.event_available_periods[event_id] or period_id in frozen_periods:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                    ])==0
                )

    # 3. Neighbors should not be placed in the same period 
    for event_id in events_in_timeblock:
        for event_id2 in problem.G.neighbors(event_id):
            if event_id2 in events_in_timeblock:
                for period_id in range(problem.P):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])+
                        sum([
                            xvars[(event_id2,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])<=1
                    )
            else:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,solution_hint[event_id][0])]
                        for room_id in range(problem.R)
                    ])==0
                )

    # 4. HPE relations
    if PRF.has_extra_constraints(problem_formulation=problem.formulation):
        for event_id in events_in_timeblock:
            for event_id2 in problem.events[event_id]['HPE']:
                if event_id2 in events_in_timeblock:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])<sum([
                            xvars[(event_id2,room_id,period_id)]*period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])
                    )
                else:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]*period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])<solution_hint[event_id2][0]
                    )
    
    # 5. For every event in the period three or more consecutive events are forbidden
    for period_id in range(Problem.P):
        model.Add(
            sum([
                xvars[(event_id,room_id,period_id)]
                for event_id in events_in_timeblock
                for room_id in range(problem.R)
            ])<3
        )

    single_event_days={(student_id,day):model.NewBoolVar(name=f'SE_{student_id}_{day}') for student_id in partial_students_set for day in range(problem.days)}
    consecutive_events={(student_id,day,i):model.NewBoolVar(name=f'{student_id}_{day}_{i}') for student_id in partial_students_set for day in range(problem.days) for i in range(3,10)}

    for student_id in partial_students_set:
        for day in range(problem.days):
            model.Add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for room_id in range(problem.R)
                    for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                ])==1
            ).OnlyEnforceIf(single_event_days[(student_id,day)])

            model.Add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for room_id in range(problem.R)
                    for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                ])!=1
            ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
            
            for i in range(3,10):
                for day_period in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-i+1):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in events_in_timeblock
                            for room_id in range(problem.R)
                            for period_id in range(day_period,day_period+i)
                        ])==i
                    ).OnlyEnforceIf(consecutive_events[(student_id,day,i)])

                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in events_in_timeblock
                            for room_id in range(problem.R)
                            for period_id in range(day_period,day_period+i)
                        ])!=i
                    ).OnlyEnforceIf(consecutive_events[(student_id,day,i)].Not())

    objective=[
        sum([single_event_days[(student_id,day)] for student_id in partial_students_set for day in range(problem.days)]),
        sum([consecutive_events[(student_id,day,i)] for student_id in partial_students_set for day in range(problem.days) for i in range(3,10)]),
        sum([xvars[(event_id,room_id,period_id)] for event_id in events_in_timeblock for room_id in range(problem.R) for period_id in problem.last_period_per_day])
    ]    

    model.Minimize(sum(objective))

    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=timesol
    solver.parameters.num_search_workers=os.cpu_count()
    solver.parameters.log_search_progress=True
    status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
    solution_subset={}
    if status in [cp_model.FEASIBLE,cp_model.OPTIMAL]:
        for (event_id,room_id,period_id),dvar in xvars.items():
            if solver.Value(dvar)==1:
                solution_subset[event_id]=(period_id,room_id)
    return solution_subset