from solvers import create_timetable,solve
from pe import Problem,PRF,Solution
from time import time
import pickle
from heuristics import TabuSearch


def scenario1():
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
        solution.set_solution(create_timetable(problem=solution.problem,csolver='gurobi',save=None))
        solution.validator()
        print(f'Operation time:{time()-start_timer}\'s')

if __name__=='__main__':
    # scenario1()
    # scenario2()
    scenario3()