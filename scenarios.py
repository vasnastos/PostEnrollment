from solvers import create_timetable,solve
from pe import Problem,PRF
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


if __name__=='__main__':
    # scenario1()
    scenario2()