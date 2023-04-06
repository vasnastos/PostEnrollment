from pe import Problem,PRF
from ortools.sat.python import cp_model
import os,gurobipy as gp


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

def optimize_rooms(problem:Problem,room_:int,solution_hint:dict,csolver='cp-sat',timesol=600):
    eset=[event_id for event_id in range(problem.E) if solution_hint[event_id]['R']==room_]
    shints=problem.create_hints(eset=eset,solution_hint=solution_hint)
    partial_student_set=list(set([student_id for event_id in eset for student_id in problem.students[event_id]['S']]))
    generated_solution=dict()

    if csolver=='cp-sat':
        model=cp_model.CpModel()
        xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in range(problem.P)}

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
                if room_id not in problem.event_available_rooms[event_id] or room_id==room_:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
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
        
        for room_id in range(problem.R):
            if room_id==room_: continue
            for period_id in range(problem.P):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in eset
                    ])<=1
                )
        
        for event_id in eset:
            for neighbor_id in list(problem.G.neighbors(event_id)):
                if event_id in eset:
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
                else:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])!=solution_hint[neighbor_id]['P']
                    )

        if PRF.has_extra_constraints(problem.formulation):
            for event_id in eset:
                for event_id2 in problem.events[event_id]['HPE']:
                    if event_id2 in eset:
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
                    else:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)] * period_id
                                for room_id in range(problem.R)
                                for period_id in range(problem.P)
                            ])<solution_hint[(event_id2,room_id,period_id)]['P']
                        )
       
        single_event_days={(student_id,day):model.NewBoolVar(name=f'hdv_{student_id}_{day}') for student_id in partial_student_set for day in range(problem.days)}
        consecutive_events={(student_id,day,i):model.NewBoolVar(name=f'hdv_{student_id}_{day}_{i}') for student_id in partial_student_set for day in range(problem.days) for i in range(3,10)}

        for student_id in partial_student_set:
            student_events=[event_id for event_id in problem.students[event_id]['S'] if event_id in eset]
            for day in range(problem.days):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in student_events
                        for room_id in range(problem.R)
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                    ])==1
                ).OnlyEnforceIf(single_event_days[(student_id,day)])

                model.Add(
                    
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in student_events
                        for room_id in range(problem.R)
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                    ])!=1
                ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
            
            for i in range(3,10):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day-i+1):
                    previous_period_cost=0
                    next_period_cost=0
                    if period_id>day*problem.periods_per_day:
                        previous_period_cost=shints[student_id][period_id-1]
                    if period_id<day*problem.periods_per_day-i+1:
                        next_period_cost=shints[student_id][period_id+i]+sum([xvars[(event_id,room_id,period_id+i)] for event_id in student_events for room_id in range(problem.R) ])
                    model.Add(
                        previous_period_cost
                        -sum([
                            xvars[(event_id,room_id,pid)]
                            for event_id in student_events
                            for room_id in range(problem.R)
                            for pid in range(period_id,period_id+i)
                        ])
                        -sum([
                            shints[student_id][pid]
                            for pid in range(period_id,period_id+i)
                        ])
                        +next_period_cost
                        +consecutive_events[(student_id,day,i)]<=-(i-1)
                    )

        objective=[
            sum([single_event_days[(student_id,day)] for student_id in partial_student_set for day in range(problem.days)]),
            sum([consecutive_events[(student_id,day,i)]*(i-2) for student_id in partial_student_set for day in range(problem.days) for i in range(3,10)]),
            sum([xvars[(event_id,room_id,period_id)] for event_id in eset for room_id in range(problem.R) for period_id in problem.last_period_per_day])
        ]

        model.Minimize(sum(objective))
        solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds=timesol
        solver.parameters.num_search_workers=os.cpu_count()
        status=solver.Solve(model=model,solution_callback=cp_model.ObjectiveSolutionPrinter())
        if status in [cp_model.FEASIBLE,cp_model.OPTIMAL]:
            for (event_id,room_id,period_id),dvar in xvars.items():
                if solver.Value(dvar)==1:
                    generated_solution[event_id]=(period_id,room_id)

    elif csolver=='gurobi':
        model=gp.Model(name='Room optimizer')

        xvars=model.addVars([(event_id,room_id,period_id) for event_id in eset for room_id in range(problem.R) for period_id in range(problem.P)])

        for event_id in eset:
            model.addConstr(
                xvars.sum(event_id,'*','*')==1
            )
        
        for event_id in eset:
            for room_id in range(problem.R):
                if room_id not in problem.event_available_rooms[event_id]:
                    model.addConstr(
                        xvars.sum(event_id,room_id,'*')==0
                    )
            
            for period_id in range(problem.P):
                if period_id not in problem.event_available_periods[event_id]:
                    model.addConstr(
                        xvars.sum(event_id,'*',period_id)==0
                    )
        
        for room_id in range(problem.R):
            for period_id in range(problem.P):
                model.addConstr(
                    xvars.sum('*',room_id,period_id)<=1
                )
        
        for event_id in eset:
            for neighbor_id in problem.G.neighbors(event_id):
                if neighbor_id in eset:
                    for period_id in range(problem.P):
                        model.addConstr(
                            xvars.sum(event_id,'*',period_id)
                            +xvars.sum(neighbor_id,'*',period_id)
                            <=1            
                        )
                else:
                    model.addConstr(
                        xvars.sum(event_id,'*',solution_hint[event_id]['P'])==0
                    )
        
        if PRF.has_extra_constraints(problem.formulation):
            for event_id in eset:
                for event_id2 in problem.events[event_id]['HPE']:
                    if event_id2 in eset:
                        model.addConstr(
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
        
        single_event_days=model.addVars([(student_id,day) for student_id in partial_student_set for day in range(problem.days)])
        consecutive_events=model.addVars([(student_id,day,i) for student_id in partial_student_set for day in range(problem.days) for i in range(3,10)])
        shints=problem.create_hints(eset,solution_hint)

        for student_id in partial_student_set:
            student_event_set=[event_id for event_id in problem.students[event_id]['S'] if event_id in eset]
            for day in range(problem.days):
                model.addConstr(
                    (
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in student_event_set
                            for room_id in range(problem.R)
                            for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day)
                        ])+sum([
                            shints[student_id][period_id]
                        ])==1
                    )>>single_event_days[(student_id,day)]==1
                )

                model.addConstr(
                    (
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in student_event_set
                            for room_id in range(problem.R)
                            for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day)
                        ])+sum([
                            shints[student_id][period_id]
                        ])!=1
                    )>>single_event_days[(student_id,day)]==0
                )
            
            for i in range(3,10):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day-i+1):
                    previous_period_cost=0
                    next_period_cost=0
                    if period_id>day*problem.periods_per_day:
                        previous_period_cost=shints[student_id][period_id]+sum([xvars[(event_id,room_id,period_id)] for event_id in eset for room_id in range(problem.R) for period_id in range(problem.P)])
                    if period_id<day*problem.periods_per_day+problem.periods_per_day-i:
                        next_period_cost=shints[student_id][period_id]+sum([xvars[(event_id,room_id,period_id)] for event_id in eset for room_id in range(problem.R) for period_id in range(day*problem.periods_per_day+day*problem.periods_per_day+problem.periods_per_day)])

                    model.addConstr(
                        previous_period_cost
                        -sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in eset
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])
                        -sum([
                            shints[student_id][period_id]
                            for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                        ])
                        +next_period_cost
                        +consecutive_events[(student_id,day,i)]<=-(i-1)
                    )

            objective=[
                single_event_days.sum('*','*'),
                sum([consecutive_events[(student_id,day,i)] * (i-1) for student_id in partial_student_set for room_id in range(problem.R) for period_id in range(problem.P)]),
                sum([xvars[(event_id,room_id,period_id)] * len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R) for period_id in range(problem.P)])
            ]

            model.setObjective(sum(objective))
            model.Params.TimeLimit=timesol
            model.Params.Threads=os.cpu_count()
            model.optimize()

            if model.Status in [gp.GRB.OPTIMAL,not gp.GRB.INFEASIBLE]:
                for (event_id,room_id,period_id),decision_var in xvars.items():
                    if decision_var.X==1:
                        generated_solution[event_id]=(period_id,room_id)
        
        return generated_solution

# def solution_cropper(problem:Problem,days_subset,solution_hint:dict,timesol=600):
#     model=cp_model.CpModel()
#     periods=[]
#     for day in days_subset:
#         count=1
#         for period in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
#             if count%3!=0:
#                 periods.append(period)
#     eset=[event_id for event_id,(period_id,_) in solution_hint.items() if period_id in periods]
#     xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in periods}

#     for event_id in eset:
#         model.Add(
#             sum([
#                 xvars[(event_id,room_id,period_id)]
#                 for room_id in range(problem.R)
#                 for period_id in range(problem.P)
#             ])==1
#         )
    
#     for event_id in eset:
#         for room_id in range(problem.R):
#             if room_id not in problem.event_available_rooms[event_id]:
#                 model.Add(
#                     sum([
#                         xvars[(event_id,room_id,period_id)]
#                         for period_id in periods
#                     ])==0
#                 )
        
#         for period_id in periods:
#             if period_id not in problem.event_available_periods[event_id]:
#                 model.Add(
#                     sum([
#                         xvars[(event_id,room_id,period_id)]
#                         for room_id in range(problem.R)
#                     ])==0
#                 )