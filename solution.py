import pe
from collections import defaultdict
import random,time


class Solution:
    def __init__(self,ds_name):
        self.solution_set=dict()
        self.roomwise_solutions=defaultdict(list)
        self.periodwise_solutions=defaultdict(list)
        self.room_period_availability=defaultdict(dict)
        self.cost=0

        for pid in range(self.R):
            for rid in range(self.P):
                self.room_period_availability[rid][pid]=False

        random.seed(time.time())
        self.problem=pe.Problem()
    
    def compute_cost(self):
        self.cost=0

    def can_be_moved(self,event_id,period_id,excluded=[]):
        pass

    def room_available(self,period_id,room_id,excluded=[]):
        

    def transfer_event(self):
        potential_solution={}
        event_id=random.rand_int(0,self.problem.E-1)
        event_neighbors=self.problem.G.neighbors(event_id)
        while len(event_neighbors)==0 or len(event_neighbors)==1:
            event_id=random.rand_int(0,self.problem.E-1)
            event_neighbors=self.problem.G.neighbors(event_id)

        for neighbor_id in event_neighbors:
            if self.can_be_moved(event_id,self.solution_set[neighbor_id][0],excluded={neighbor_id}):
                potential_solution[event_id]=self.solution_set[neighbor_id][0]
                break
        
        return potential_solution
    
    def swap_events(self):
        potential_move=dict()
        event_id=random.rand_int(0,self.problem.E-1)
        event_neighbors=self.problem.G.neighbors(event_id)
        while len(neighbors)==0:
            event_id=random.rand_int(0,self.problem.E-1)
            neighbors=self.problem.G.neighbors(event_id)
        
        for event_id2 in event_neighbors:
            if self.can_be_moved(event_id,self.solution_set[event_id2][0],excluded=[event_id2]) and self.can_be_moved(event_id2,self.solution_set[event_id][0],excluded=[event_id]):
                potential_move={
                    event_id:[self.solution_set[event_id2][0],-1],
                    event_id2:[self.solution_set[event_id][0],-1]
                }

            for room_id in range(self.problem.R):
                if self.can_be_moved()

