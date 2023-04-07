
from arena import Arena
from heuristics import SimulatedAnnealing
from solution import Solution

def scenario1():
    """
        Execute a simulated Annealing procedure
        using Transfer, Swap, Kempe and Kick Operator
    """
    instances=[
        # "med_1.tim",
        # "med_2.tim",
        # "med_3.tim",
        # "med_4.tim",
        # "med_5.tim",
        # "med_6.tim",
        # "med_7.tim",
        # "med_8.tim",
        # "med_9.tim",
        # "med_10.tim",
        # "med_11.tim",
        # "med_12.tim",
        # "med_13.tim",
        # "med_14.tim",
        # "med_15.tim",
        # "med_16.tim",
        # "med_17.tim",
        # "med_18.tim",
        # "med_19.tim",
        # "med_20.tim",
        'easy01.tim'
    ]
    
    arena=Arena()
    for instance in instances:
        sa_obj=SimulatedAnnealing(instance)
        sa_obj.solve()
        arena.add(dataset_id=instance,events=sa_obj.solution.problem.E,rooms=sa_obj.solution.problem.R,density=sa_obj.solution.problem.conflict_density)
    arena.save()

def scenario2():
    import os
    instances=[
        "easy01.tim",
        "easy02.tim",
        "easy03.tim",
        "easy04.tim",
        "easy05.tim"
    ]

    for instance in instances:
        sa_obj=Solution(instance)
        sol=sa_obj.solve_exact(solution_hint=False,timesol=600)
        sa_obj.set_solution(sol)
        sa_obj.save(os.path.join(f'','results',f'{instance.removesuffix(".tim")}_{sa_obj.compute_cost()}.sln'))


def scenario3():
    instances=[
        "o01.tim",
        "o02.tim",
        "o03.tim",
        "o04.tim",
        "o05.tim",
        "o06.tim",
        "o07.tim",
        "o08.tim",
        "o09.tim",
        "o010.tim",
        "o011.tim",
        "o012.tim",
        "o013.tim",
        "o014.tim",
        "o015.tim",
        "o016.tim",
        "o017.tim",
        "o018.tim",
        "o019.tim",
        "o020.tim",
    ]

    arena=Arena()
    for instance in instances:
        sa=SimulatedAnnealing(instance)
        sa.solve(timesol=3000)
        sa.save()
        arena.add(instance,sa.solution.problem.E,sa.solution.problem.R,sa.solution.problem.conflict_density,sa.solution.compute_cost())
    arena.save()

if __name__=='__main__':
    # scenario1()
    scenario2()