from ortools.sat.python import cp_model
from pe import Problem,PRF
import os

def full_solver(problem:"Problem",solution_hint=None,timesol=600):
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
    solution_set={}
    if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
        for (event_id,room_id,period_id),dvar in xvars.items():
            if solver.Value(dvar)==1:
                solution_set[event_id]=(period_id,room_id)
    
    return solution_set

def day_by_day(problem:"Problem",day:int,solution_hint:dict,timesol=60):
    eset=[event_id for event_id,(period_id,_) in solution_hint.items() if period_id%problem.periods_per_day==day]
    periods=list(range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day))
    partial_students=set([student_id for event_id,(period_id,_) in solution_hint.items() for student_id in problem.events[event_id]['S'] if period_id%problem.periods_per_day==day])


    model=cp_model.CpModel()
    xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'v{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem) for period_id in periods}

    if solution_hint:
        for event_id,(period_id,room_id) in solution_hint.items():
            if event_id in eset:
                model.AddHint(xvars[(event_id,room_id,period_id)],1)
    
    # 1. All events should placed in exact one period
    for event_id in eset:
        model.Add(
            sum([
                xvars[(event_id,room_id,period_id)]
                for room_id in range(problem.R)
                for period_id in periods
            ])==1
        )
    
    # 2. Events should not be placed in periods or rooms that are not suitable
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

    # 3. Neighbor events should not be placed in the same period
    for event_id in eset:
        for event_id2 in problem.G.neighbors(event_id):
            if event_id2 in eset:
                for period_id in periods:
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

    # 4. If the extra constraints are enabled
    if PRF.has_extra_constraints(problem.formulation):
        for event_id in eset:
            for period_id in periods:
                if period_id not in problem.event_available_periods[event_id]:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])==0
                    )
        
        for event_id in eset:
            for event_id2 in problem.events[event_id]['HPE']:
                if event_id2 in eset:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]*period_id
                            for room_id in range(problem.R)
                            for period_id in periods
                        ])<
                        sum([
                            xvars[(event_id,room_id,period_id)]*period_id
                            for room_id in range(problem.R)
                            for period_id in periods
                        ])
                    )
    
    # 5. Soft constrains
    consecutive_events={(student_id,consecutive_events):model.NewBoolVar(name=f'{student_id}_{consecutive_events}') for student_id in partial_students for i in range(3,10)}
    for student_id in partial_students:
        for i in range(3,10):
            for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-i-1):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,pcurrent)]
                        for event_id in eset
                        for room_id in range(problem.R)
                        for pcurrent in range(period_id,period_id+i)
                    ])==i
                ).OnlyEnforceIf(consecutive_events[(student_id,i)])
    
    objective=[
        sum([consecutive_events[(student_id,i)] for student_id in partial_students for i in range(3,10)]),
        sum([xvars[(event_id,room_id,day*problem.periods_per_day+problem.periods_per_day-1)] for event_id in eset for room_id in range(problem.R)])
    ]

    model.Minimize(sum(objective))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=timesol
    solver.parameters.num_search_workers=os.cpu_count()
    status=solver.Solve(model)
    solution_set={}
    if status in [cp_model.FEASIBLE,cp_model.OPTIMAL]:
        for (event_id,room_id,period_id),dvar in xvars.items():
            if solver.Value(dvar)==1:
                solution_set[event_id]=(period_id,room_id)
    return solution_set

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


def partial_room_solver(problem:"Problem",moves:dict,solution_hint=None):
    periods=list(set(moves.values()))
    
    model=cp_model.CpModel()
    sol_vars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in moves.keys() for room_id in range(problem.R) for period_id in periods}

    for event_id,period_id in moves.items():
        model.Add(
            sum([sol_vars[(event_id,room_id,period_id)] for room_id in range(problem.R)])==1
        )

    for event_id,period_id in moves.items():
        for period_id2 in periods:
            if period_id==period_id2: continue
            model.Add(
                sum([sol_vars[(event_id,room_id,period_id2)] for room_id in range(problem.R)])==0
            )

    for room_id in range(problem.R):
        model.Add(
            sum([sol_vars[(event_id,room_id,period_id)] for event_id in list(moves.keys()) for period_id in periods])<=1
        )
    
