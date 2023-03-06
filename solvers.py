from ortools.sat.python import cp_model
from pe import Problem

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
