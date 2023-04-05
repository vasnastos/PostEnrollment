from solvers import create_timetable,solve
from pe import Problem,PRF,Solution
from time import time
import pickle,random
from heuristics import TabuSearch,SimulatedAnnealing
import argparse

class Configuration:
    def __init__(self):
        self.solvers=['gurobi','cpsat','cpsat']
        self.timestamps=[800,1900,60,200]
    
    def parse(self):
        self.parser=argparse.ArgumentParser(prog='Post Enrollment Timetabling available arguments')
        self.parser.add_argument('--isolver','--in',default=600)
        self.parser.add_argument('--dbdsolver','--dbd',default=60)
        self.parser.add_argument('--dcsolver','--dc',default=200)
        self.parser.add_argument('--itype','--it',default='cp-sat')
        self.parser.add_argument('--dbdtype','--dbdt',default='cp-sat',choices=['cp-sat','cplex','gurobi'])
        self.parser.add_argument('--dctype','--dct',default='cp-sat',choices=['cp-sat','cplex','gurobi'])
        self.parser.add_argument('--sasolver','--sa',default=1900)
    
    def set_vars(self):
        pass



def scenario1():
    """
        Construct initial solutions
    """
    instances=Problem.get_instances()
    counters={}

    for instance in instances:
        problem=Problem()
        problem.read(instance)
        problem.statistics()

        start_timer=time()
        initial_solution=create_timetable(problem=problem,csolver='cp-sat',timesol=600)
        counters[(problem.id,'cp-sat')]=time()-start_timer

    with open('create_timetable_init_times.pickle','wb') as binary_writer:
        pickle.dump(counters,binary_writer)


def scenario2():
    """
        Try the tabu search formulation scenario
    """
    instances=Problem.get_instances(formulations=[PRF.MetaheuristicsNetwork,PRF.HarderLewisPaechter])
    for instance in instances:
        ts=TabuSearch(instance)
        _=ts.TS()

def scenario3():
    """
        Run day by day scenario using the appropriate arguments example
    """
    instance_name=f'easy03.tim'
    solution=Solution(instance_name)
    
    init_solution=create_timetable(problem=solution.problem,csolver='cp-sat')
    if init_solution!={}:
        solution.set_solution(init_solution)
    day=random.randint(0,solution.problem.days-1)
    

    print(solve(problem=solution.problem,tsolver='cp-sat',day_by_day=True,init_solution=init_solution,solution_hint=init_solution,day=day))

def scenario4():
    """
        Test days combined Solver
    """
    instance_name="easy03.tim"
    solution=Solution(instance_name)
    days=[0,1,4]
    init_solution=create_timetable(problem=solution.problem,csolver='gurobi')
    if init_solution!={}:
        solution.set_solution(init_solution)

    retrieved_solution=solve(problem=solution.problem,days_combined=True,days=days,solution_hint=solution.solution_set)
    solution.set_solution(retrieved_solution)
    solution.validator()

def scenario5():
    instances=[
        "small_1.tim",
        "small_2.tim",
        "small_3.tim",
        "small_4.tim",
        "small_5.tim",
        "small_6.tim",
        "small_7.tim",
        "small_8.tim",
        "small_9.tim",
        "small_10.tim",
        "small_11.tim",
        "small_12.tim",
        "small_13.tim",
        "small_14.tim",
        "small_15.tim",
        "small_16.tim",
        "small_17.tim",
        "small_18.tim",
        "small_19.tim",
        "small_20.tim",
        "medium01.tim",
        "medium02.tim",
        "medium03.tim",
        "medium04.tim",
        "medium05.tim"
    ]

    for instance in instances:
        solution=Solution(instance)
        start_timer=time()
        solution.set_solution(create_timetable(problem=solution.problem,csolver='gurobi',save=None,timesol=500))
        solution.validator()
        print(f'Operation time:{time()-start_timer}\'s')

def scenario6():
    """
    Test simulated Annealing procedure
    """
    # instances=[
    #     'big_1.tim',
    #     'big_2.tim',
    #     'big_3.tim',
    #     'big_4.tim',
    #     'big_5.tim',
    #     'big_6.tim',
    #     'big_7.tim',
    #     'big_8.tim',
    #     'big_9.tim',
    #     'big_10.tim',
    #     'big_11.tim',
    #     'big_12.tim',
    #     'big_13.tim',
    #     'big_14.tim',
    #     'big_15.tim',
    #     'big_16.tim',
    #     'big_17.tim',
    #     'big_18.tim',
    #     'big_19.tim',
    #     'big_20.tim',
    # ]

    instances=[
        "easy01.tim",
        "easy02.tim",
        "easy03.tim",
        "easy04.tim",
        "easy05.tim"
    ]

    for instance in instances:
        start_timer=time()
        sa=SimulatedAnnealing(instance)
        sa.solution.problem.statistics()
        sa.solve()
        print(f'Operation time:{time()-start_timer}\'s')

def scenario7():
    """
        Find Frozenrooms for each dataset
    """
    instance='big_2.tim'
    problem=Problem()
    problem.read(instance)
    print(problem.frozenrooms())

if __name__=='__main__':
    # scenario1()
    # scenario2()
    # scenario3()
    # scenario4() 
    # scenario5()
    scenario6()
    # scenario7()
