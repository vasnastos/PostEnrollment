from base import Core,Configuration
from solvers import Solution,Mathematical_Solver,simulated_annealing

def scenario1():
    config=Configuration()
    print(str(config))
    dataset_name='i01.tim'
    solution=Solution(dataset_name)
    simulated_annealing(solution,config)
    

def scenario2():
    config=Configuration()
    print(config)
    for dataset_name in config.instances:
        print(f'{dataset_name=}')
        solution=Solution(dataset_name)
        simulated_annealing(solution,config)
        solution.save()
        solution.feasibility()

def scenario3():
    dataset_name='small_1.tim'
    solution=Solution(dataset_name)
    solution.set_(Mathematical_Solver.generate_solution(solution.problem,solver_type='gurobi'),init=True)
    solution.feasibility()

def scenario4():
    dataset='o02.tim'
    solution=Solution(dataset)
    solution.read()
    icost=solution.compute_cost()
    print(f'{icost=}')

    for day in range(Core.days):
        print(f'Day:{day}\tCost:{solution.compute_day_cost(day)}/{icost}')
        eset=[event_id for event_id,(period_id,_) in solution.events_solution.items() if period_id//Core.periods_per_day==day]
        esol=Mathematical_Solver.day_by_day(solution.problem,eset,day,{event_id:solution.events_solution[event_id] for event_id in eset},solver_type='gurobi',time_limit=40)
        if esol!={}:
            solution.set_(esol)
        print(f'New Cost:{solution.compute_cost()}')
    
    print(f'{solution.compute_cost()=}')
    solution.save()


def scenario6():
    from itertools import combinations
    day_combinations=combinations(list(range(Core.days)),2)
    config=Configuration()
    for dataset_name in config.instances:
        solution=Solution(dataset_name)
        simulated_annealing(solution,config)
        solution.save()




if __name__ == '__main__':
    # scenario1() # Distinct Dataset test
    # scenario2() # Solve all the datasets
    # scenario3() # Test gurobi mip version of the problem  
    # scenario4() # Test day by day example
    # scenario5() # Test days combined solver
    scenario6() # reduce day by already solved instances
