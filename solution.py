import pe
from collections import defaultdict
import random,time

from queue import LifoQueue


class Solution:
    def __init__(self,ds_name):
        self.solution_set=dict()
        self.roomwise_solutions=defaultdict(list)
        self.periodwise_solutions=defaultdict(list)
        self.room_period_availability=defaultdict(dict)
        self.cost=0
        random.seed(time.time())
        self.problem=pe.Problem()
    
    def compute_cost(self):
        self.cost=0

        # Cost computation calculation


    def can_be_moved(self,event_id,period_id,excluded=[]):
        for neighbor_id in self.problem.G.neighbors(event_id):
            if neighbor_id in excluded: continue
            if period_id==self.solution_set[neighbor_id][0]:
                return False
        return True

    def room_available(self,period_id,room_id,excluded=[]):
        for event_id in self.roomwise_solutions[room_id]:
            if event_id in excluded:
                continue
            if period_id==self.solution_set[event_id][0]:
                return False
        return True

    def transfer_event(self):
        event_id=random.rand_int(0,self.problem.E-1)
        event_neighbors=self.problem.G.neighbors(event_id)
        while len(event_neighbors)==0 or len(event_neighbors)==1:
            event_id=random.rand_int(0,self.problem.E-1)
            event_neighbors=self.problem.G.neighbors(event_id)

        candicate_period=None
        for neighbor_id in event_neighbors:
            if self.can_be_moved(event_id,self.solution_set[neighbor_id][0],excluded={neighbor_id}):
                candicate_period=self.solution_set[neighbor_id][0]
                break
        
        
        if candicate_period:
            for room_id in range(self.problem.R):
                if self.room_available(room_id,candicate_period):
                    return {event_id:(candicate_period,room_id)}

        return dict()
    
    def swap_events(self):
        potential_move=dict()
        event_id=random.rand_int(0,self.problem.E-1)
        event_neighbors=self.problem.G.neighbors(event_id)
        while len(neighbors)==0:
            event_id=random.rand_int(0,self.problem.E-1)
            neighbors=self.problem.G.neighbors(event_id)
        
        for event_id2 in event_neighbors:
            if self.can_be_moved(event_id,self.solution_set[event_id2][0],excluded=[event_id2]) and self.can_be_moved(event_id2,self.solution_set[event_id][0],excluded=[event_id]):
                # 1. Swap the rooms for two events
                if self.solution_set[event_id2][1] in self.problem.event_available_rooms[event_id] and self.solution_set[event_id][1] in self.problem.event_available_rooms[event_id2]:
                    return {
                        event_id:(self.solution_set[event_id2][0],self.solution_set[event_id2][1]),
                        event_id2:(self.solution_set[event_id][0],self.solution_set[event_id][1])
                    }
                
                # 2. Keep the same rooms
                elif self.room_available(self.solution_set[event_id2][0],self.solution_set[event_id][1]) and self.room_available(self.solution_set[event_id][0],self.solution_set[event_id2][1]):
                    return {
                        event_id:(self.solution_set[event_id2][0],self.solution_set[event_id][1]),
                        event_id2:(self.solution_set[event_id][0],self.solution_set[event_id2][1])
                    }

                # 3. Find a suitable room
                else:
                    # event_id1 room
                    for room_id in self.problem.event_available_rooms[event_id]:
                        if room_id in [self.solution_set[event_id][1],self.solution_set[event_id2]]:
                            continue
                        if self.room_available(self.solution_set[event_id2][0],room_id):
                            potential_move[event_id]=(self.solution_set[event_id2][0],room_id)
                    
                    if event_id not in potential_move: 
                        potential_move.clear()
                        continue

                    for room_id in self.problem.event_available_rooms[event_id2]:
                        if room_id in [self.solution_set[event_id][1],self.solution_set[event_id2]]:
                            continue
                        if self.room_available(self.solution_set[event_id][0],room_id):
                            potential_move[event_id]=(self.solution_set[event_id2][0],room_id)

                    if event_id2 not in potential_move: 
                        potential_move.clear()
                        continue
                
        return potential_move

    def kempe_chain(self):
        kc=LifoQueue()
        event_id1=random.randint(0,self.problem.E-1)
        eneighbors=self.problem.G.neighbors(event_id1)
        while len(eneighbors)==0:
            event_id1=random.randint(0,self.problem.E-1)
            eneighbors=self.problem.G.neighbors(event_id1)

        event_id2=eneighbors[random.randint(0,len(eneighbors)-1)]
        
        versus_periods={
            self.solution_set[event_id1][0]:self.solution_set[event_id2][0],
            self.solution_set[event_id2][0]:self.solution_set[event_id1][0]
        }

        moves=dict()
        kc.put(event_id1)
        while not kc.empty():
            current_event=kc.get()
            current_period=self.solution_set[current_event][0]
            new_period=versus_periods[current_period]
            moves[current_event]=new_period
            eneighbors=self.problem.G.neioghbors(current_event)
            for neighbor in eneighbors:
                if neighbor in moves: continue
                if self.solution_set[neighbor][0]==new_period:
                    kc.put(neighbor)
        
        potential_solution={}
        for event_id,period_id in moves.items():
            found=False
            for room_id in range(self.problem.R):
                if self.room_available(period_id,room_id,excluded=[event_id]):
                    potential_solution[event_id]=(period_id,room_id)
            if not found:
                return dict()
        return potential_solution


if __name__=='__main__':
    pass


