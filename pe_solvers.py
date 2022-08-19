from ortools.sat.python import cp_model
from docplex.mp.model import Model
import docplex.cp.model as cpx
import os

from pe import Problem,PPD,D,P

def hints(problem,eset,solution):
    shints={student_id:{p:False for p in range(P)} for student_id in problem.students.keys()}
    for student_id,student_events in problem.students.items():
        for e in student_events:
            if e in eset: continue
            shints[student_id][solution[e][1]]=True

    return shints


def pe_solver_partially(problem:Problem,timesol=600):
    model=cp_model.CpModel()
    dparams={(eid,rid,pid):model.NewBoolVar(name=f'problem_{eid}_{rid}_{pid}') for eid in range(problem.E) for rid in range(problem.event_rooms[eid]) for pid in problem.events[eid]['P']} 

    for eid in range(problem.E):
        model.Add(sum([dparams[(eid,rid,pid)] for rid in problem.event_rooms[eid] for pid in problem.events[eid]['P']])<=1)
    
    for rid in range(problem.R):
        for pid in range(P):
            model.Add(sum([dparams[(eid,rid,pid)] for eid in range(problem.E) if rid in problem.event_rooms[eid] and pid in problem.events[eid]['P']])<=1)
    
    for eid in range(problem.E):
        for eid2 in problem.G.neighbors(eid):
            for pid in range(P):
                if pid not in problem.events[eid]['P'] or pid not in problem.events[eid2]['P']: continue
                model.Add(sum([dparams[(eid,rid,pid)] for rid in problem.event_rooms[eid]])+sum([dparams[(eid2,rid,pid)] for rid in problem.event_rooms[eid2]])<=1)
    
    model.Maximize(sum([dparams[(eid,rid,pid)]*len(problem.events[eid]['S']) for eid in range(problem.E) for rid in problem.event_rooms[eid] for pid in problem.events[eid]['P']]))

    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=timesol
    solver.parameters.num_search_workers=os.cpu_count()
    status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())

    solved_events={}
    unsolved_events=[]

    if status==cp_model.FEASIBLE or status==cp_model.OPTIMAL:
        for (eid,rid,pid),dvar in dparams.items():
            if solver.Value(dvar)==1:
                solved_events[eid]=(rid,pid)
            else:
                unsolved_events.append(eid)
    
    return solved_events,unsolved_events

def pe_solver1(problem:Problem,objectiveV=True,timesol=600):
    model=cp_model.CpModel()
    dparams={(eid,rid,pid):model.NewBoolVar(name=f'problem_{eid}_{rid}_{pid}') for eid in range(problem.E) for rid in range(problem.event_rooms[eid]) for pid in problem.events[eid]['P']} 

    for eid in range(problem.E):
        model.Add(sum([dparams[(eid,rid,pid)] for rid in problem.event_rooms[eid] for pid in problem.events[eid]['P']])==1)
    
    for rid in range(problem.R):
        for pid in range(P):
            model.Add(sum([dparams[(eid,rid,pid)] for eid in range(problem.E) if rid in problem.event_rooms[eid] and pid in problem.events[eid]['P']])<=1)

    for pid in range(P):
        model.Add(sum([dparams[(eid,rid,pid)] for eid in range(problem.E) for rid in range(problem.R) if pid in problem.events[eid]['P']])<=problem.R)
    
    for eid in range(problem.E):
        for eid2 in problem.G.neighbors(eid):
            for pid in range(P):
                if pid not in problem.events[eid]['P'] or pid not in problem.events[eid2]['P']: continue
                model.Add(sum([dparams[(eid,rid,pid)] for rid in problem.event_rooms[eid]])+sum([dparams[(eid2,rid,pid)] for rid in problem.event_rooms[eid2]])<=1)
    
    if objectiveV:
        single_day_events={(student_id,d):model.NewBoolVar(name=f'single_day_events_{eid}_{d}') for student_id in range(problem.S) for d in range(D)}
        consecutive_events={(student_id,d,i):[model.NewBoolVar(name=f'consecutive_events_{student_id}_{d}_{i}_0'),model.NewBoolVar(name=f'consecutive_events_{student_id}_{d}_{i}_1')] for student_id in range(D) for i in range(3,5)}
        consecutive_events.update({(student_id,d,i):model.NewBoolVar(name=f'consecutiove_events_{student_id}_{d}_{i}') for eid in range(problem.S) for d in range(D) for i in range(5,PPD+1)})

        for student_id in range(problem.S):
            for d in range(D):
                for p in range(D*PPD,D*PPD+PPD):
                    model.Add(
                        -sum([dparams[(eid,rid,p)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if p in problem.events[eid]['P']])
                        +sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in [px for px in range(D*PPD,D*PPD+PPD) if px!=p]])
                        +single_day_events[(student_id,d)]>=0
                    )
            for i in range(3,5):
                threshold=PPD-(i*2)
                for p in range(D*PPD,D*PPD*PPD-i+1):
                    previous_period=p-1
                    next_period=p+i
                    if previous_period<D*PPD:
                        model.Add(
                            -sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in range(p,next_period) if p in problem.events[eid]['P']])
                            +sum([dparams[(eid,rid,next_period)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if next_period in problem.events[eid]['P']])
                            +consecutive_events[(student_id,d,i)][0]>=-(i-1)
                        )
                    else:
                        model.Add(
                            sum([dparams[(eid,rid,previous_period)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if previous_period in problem.events[eid]['P']])
                            -sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in range(p,next_period) if p in problem.events[eid]['P']])
                            +sum([dparams[(eid,rid,next_period)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if next_period in problem.events[eid]['P']])
                            +consecutive_events[(student_id,d,i)][0]>=-(i-1)
                        )
                    
                    if p<threshold:
                        for p2 in range(next_period+1,D*PPD+PPD-i+1):
                            previous_period=p2-1
                            next_period2=p2+i
                            
                            if next_period2>=D*PPD+PPD:
                                model.Add(
                                    sum([dparams[(eid,rid,previous_period)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if previous_period in problem.events[eid]['P']])
                                    -sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in range(p2,next_period2)])
                                    +consecutive_events[(student_id,d,i)][1]>=-(i-1)
                                ).OnlyEnforceIf(consecutive_events[(student_id,d,i)][0])
                            else:
                                model.Add(
                                    sum([dparams[(eid,rid,previous_period)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if previous_period in problem.events[eid]['P']])
                                    -sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in range(p2,next_period2)])
                                    +sum([dparams[(eid,rid,next_period2)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if next_period2 in problem.events[eid]])
                                    +consecutive_events[(student_id,d,i)][1]>=-(i-1)
                                ).OnlyEnforceIf(consecutive_events[(student_id,d,i)][0])

            for i in range(5,PPD+1):
                for p in range(D*PPD,D*PPD+PPD-i+1):
                    previous_period=p-1
                    next_period=p+i
                    if previous_period<D*PPD:
                        if next_period>=D*PPD+PPD:
                            model.Add(
                                -sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in range(p,next_period) if p in problem.events[eid]['P']])
                                +consecutive_events[(student_id,d,i)]>=-(i-1)
                            )
                        else:
                            model.Add(
                                -sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in range(p,next_period) if p in problem.events[eid]['P']])
                                +sum([dparams[(eid,rid,next_period)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if next_period in problem.events[eid]['P']])
                                +consecutive_events[(student_id,d,i)]>=-(i-1)
                            )
                    else:
                        if next_period>=D*PPD+PPD:
                            model.Add(
                                sum([dparams[(eid,rid,previous_period)] for eid in range(problem.E) for rid in problem.event_rooms[eid] if previous_period in problem.events[eid]['Ps']])
                                -sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in range(p,next_period) if p in problem.events[eid]['P']])
                                +consecutive_events[(student_id,d,i)]>=-(i-1)
                            )
                        else:
                            model.Add(
                                sum([dparams[(eid,rid,previous_period)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if previous_period in problem.events[eid]['P']])
                                -sum([dparams[(eid,rid,pid)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] for pid in range(p,next_period) if p in problem.events[eid]['P']])
                                +sum([dparams[(eid,rid,next_period)] for eid in problem.students[student_id] for rid in problem.event_rooms[eid] if next_period in problem.events[eid]['P']])
                                +consecutive_events[(student_id,d,i)]>=-(i-1)
                            )
    
        objective=[
            sum([single_day_events[(student_id,d)] for student_id in range(problem.S) for d in range(D)])
            ,sum([consecutive_events[(student_id,d,i)][j] * (i-2) for student_id in range(problem.S) for d in range(D) for i in range(5,PPD+1) for j in [0,1]])
            ,sum([consecutive_events[(student_id,d,i)] * (i-2) for student_id in range(problem.S) for d in range(D) for i in range(5,PPD+1)])
            ,sum([consecutive_events[(eid,rid,pid)] * len(problem.events[eid]['S']) for eid in range(problem.E) for rid in problem.event_rooms[eid] for pid in problem.last_period_per_day if pid in problem.events[eid]['P']])
        ]

        model.Minimize(objective)

    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=timesol
    solver.parameters.num_search_workers=os.cpu_count()
    status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
    if status==cp_model.FEASIBLE or status==cp_model.OPTIMAL:
        esol={}
        for (eid,rid,pid),dvar in dparams.items():
            if solver.Value(dvar)==1:
                esol[eid]=(rid,pid)
    return esol

def pe_solver2(problem,timesol):
    model=cpx.CpoModel()
    dparams={(eid,rid,pid):model.binary_var(name=f'problem_{eid}_{rid}_{pid}') for eid in range(problem.E) for rid in range(problem.event_rooms[eid]) for pid in problem.events[eid]['P']}

    for eid in range(problem.E):
        model.add(sum([dparams[(eid,rid,pid)] for rid in problem.event_rooms[eid] for pid in problem.events[eid]['P']])==1)

    for rid in range(problem.R):
        for pid in range(P):
            model.add(
                sum([dparams[(eid,rid,pid)] for eid in range(problem.E)])<=1
            )    

    for eid in range(problem.E):
        for eid2 in problem.G.neighbors(eid):
            for pid in range(P):
                if pid not in problem.events[eid]['P'] or pid not in problem.events[eid]['P']: continue
                model.add(
                    sum([dparams[(eid,rid,pid)] for rid in problem.event_rooms[eid]])
                    +sum([dparams[(eid2,rid,pid)] for rid in problem.event_rooms[eid2]])
                    <=1
                )

    params=cpx.CpoParameters()
    params.LogPeriod=5000
    params.TimeLimit=timesol


    solver=model.solve(params=params)
    esol={}
    if solver:
        for (eid,rid,pid),dvar in dparams.items():
            if solver[dvar]==1:
                esol[eid]=(rid,pid)
    return esol

def pe_solver3(problem):
    # Two stage solver
    pass