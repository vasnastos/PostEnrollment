import pe
from collections import defaultdict,Counter
import random,time
from queue import LifoQueue


class Solution:
    def __init__(self,ds_name):
        self.solution_set={event_id:{"P":-1,"R":-1} for event_id in range(self.problem.E)}
        self.roomwise_solutions=defaultdict(list)
        self.periodwise_solutions=defaultdict(list)
        self.room_period_availability=defaultdict(dict)
        self.cost=0
        random.seed(time.time())
        self.problem=pe.Problem()
        self.problem.read(ds_name)
        self.memory=dict()
    
    def compute_cost(self):
        ecost=0
        # Cost computation calculation
        for student_id in range(self.S):
            consecutive=0
            student_participate_in=set([self.solution_set[event_id]["P"] for event_id in self.students[student_id]])
            for day in range(self.days):
                day_events=0
                for period_id in range(day * self.problem.periods_per_day,day * self.problem.periods_per_day+self.problem.periods_per_day):
                    if period_id in student_participate_in:
                        consecutive+=1
                        day_events+=1
                    else:
                        if consecutive>2:
                            ecost+=(consecutive-2)
                        consecutive=0
                
                if consecutive>2:
                    ecost+=(consecutive-2)
                consecutive=0

                if day_events==1:
                    ecost+=1
        
        for event_id in range(self.E):
            if self.solution_set[event_id]['P'] in self.problem.last_period_per_day:
                ecost+=len(self.problem.events[event_id]['S'])

        return ecost

    def can_be_moved(self,event_id,period_id,excluded=[]):
        for neighbor_id in self.problem.G.neighbors(event_id):
            if neighbor_id in excluded: continue
            if period_id==self.solution_set[neighbor_id]['P']:
                return False
        return True

    def room_available(self,period_id,room_id,excluded=[]):
        for event_id in self.roomwise_solutions[room_id]:
            if event_id in excluded:
                continue
            if period_id==self.solution_set[event_id]['P']:
                return False
        return True

    def schedule(self,event_id,room_id,period_id):
        partial_cost=0
        event_students=self.problem.events[event_id]['S']
        day=period_id//self.problem.periods_per_day

        for student_id in event_students:
            student_periods=[self.solution_set[event_id2]['P'] for event_id2 in self.problem.students[student_id]]
            events_in_days=Counter([period_id//self.problem.periods_per_day for period_id in  student_periods])

            if events_in_days.get(day,-1)==0:
                partial_cost+=1
                continue
            
            elif events_in_days.get(day,-1)==1 and student_periods[0]!=period_id:
                partial_cost-=1
                continue
            
            # A. Find previous consecutive cost
            consecutive=0
            for pid in range(day * self.problem.periods_per_day,day * self.problem.periods_per_day + self.problem.periods_per_day):
                if pid in student_periods:
                    consecutive+=1
                else:
                    if consecutive>2:
                        partial_cost-=(consecutive-2)
                    consecutive=0
            if consecutive>2:
                partial_cost-=(consecutive-2)
            consecutive=0

            # B. Find the consecutive cost after the addition of an extra period
            consecutive=0
            student_periods.append(period_id)

            for pid in range(day * self.problem.periods_per_day, day * self.problem.periods_per_day+self.problem.periods_per_day):
                 if pid in student_periods:
                     consecutive+=1
                 else:
                     if consecutive>2:
                         partial_cost+=(consecutive-2)
                     consecutive=0
            
            if consecutive>2:
                partial_cost+=(consecutive-2)
            consecutive=0
        
        if period_id in self.problem.last_period_per_day:
            partial_cost+=len(self.problem.events[event_id]['S'])
        
        self.periodwise_solutions[period_id].append(event_id)
        self.roomwise_solutions[room_id].append(event_id)
        self.solution_set[event_id]['P']=period_id
        self.solution_set[event_id]['R']=room_id
        return partial_cost

    def unschedule(self,event_id):
        partial_cost=0
        event_students=self.problem.events[event_id]['S']

        consecutive=0
        current_period=self.solution_set[event_id]['P']
        day=current_period//self.problem.periods_per_day
        events_in_day=Counter([self.solution_set[event_id2]['P'] for student_id in event_students for event_id2 in self.problem.students[student_id]])

        if events_in_day.get(day,-1)==1:
            partial_cost-=1
        elif events_in_day.get(day,-1)==2:
            partial_cost+=1
        else:
            # A. Find consecutive events before period deletion 
            for student_id in event_students:
                student_periods=[self.solution_set[event_id2]['P'] for event_id2 in self.problem.students[student_id]]
                consecutive=0
                for period_id in range(day * self.problem.periods_per_day, day*self.problem.periods_per_day+self.problem.periods_per_day):
                    if period_id in student_periods:
                        consecutive+=1
                    else:
                        if consecutive>2:
                            partial_cost-=(consecutive-2)
                        consecutive=0
                if consecutive>2:
                    partial_cost-=(consecutive-2)

                # B. Find consecutive events after period removal
                consecutive=0
                student_periods.remove(period_id)
                for period_id in range(day * self.problem.periods_per_day, day*self.problem.periods_per_day+self.problem.periods_per_day):
                    if period_id in student_periods:
                        consecutive+=1
                    else:
                        if consecutive>2:
                            partial_cost+=(consecutive-2)
                        consecutive=0

                if consecutive>2:
                    partial_cost+=(consecutive-2)
                consecutive=0
            
            if self.solution_set[event_id]['P'] in self.problem.last_period_per_day:
               partial_cost-=len(self.problem.events[event_id]['S']) 

        self.periodwise_solutions[self.solution_set[event_id]['P']].remove(event_id)
        self.roomwise_solutions[self.solution_set[event_id]['R']].remove(event_id)
        self.solution_set[event_id]['P']=-1
        self.solution_set[event_id]['R']=-1    
        return partial_cost

    def transfer_event(self):
        event_id=random.rand_int(0,self.problem.E-1)
        event_neighbors=self.problem.G.neighbors(event_id)
        while len(event_neighbors)==0 or len(event_neighbors)==1:
            event_id=random.rand_int(0,self.problem.E-1)
            event_neighbors=self.problem.G.neighbors(event_id)

        candicate_period=None
        for neighbor_id in event_neighbors:
            if self.can_be_moved(event_id,self.solution_set[neighbor_id]['P'],excluded={neighbor_id}):
                candicate_period=self.solution_set[neighbor_id]['P']
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
            if self.can_be_moved(event_id,self.solution_set[event_id2]['P'],excluded=[event_id2]) and self.can_be_moved(event_id2,self.solution_set[event_id]['P'],excluded=[event_id]):
                # 1. Swap the rooms for two events
                if self.solution_set[event_id2]['R'] in self.problem.event_available_rooms[event_id] and self.solution_set[event_id]['R'] in self.problem.event_available_rooms[event_id2]:
                    return {
                        event_id:(self.solution_set[event_id2]['P'],self.solution_set[event_id2]['R']),
                        event_id2:(self.solution_set[event_id]['P'],self.solution_set[event_id]['R'])
                    }
                
                # 2. Keep the same rooms
                elif self.room_available(self.solution_set[event_id2]['P'],self.solution_set[event_id]['R']) and self.room_available(self.solution_set[event_id]['P'],self.solution_set[event_id2]['R']):
                    return {
                        event_id:(self.solution_set[event_id2]['P'],self.solution_set[event_id]['R']),
                        event_id2:(self.solution_set[event_id]['P'],self.solution_set[event_id2]['R'])
                    }

                # 3. Find a suitable room
                else:
                    # event_id1 room
                    for room_id in self.problem.event_available_rooms[event_id]:
                        if room_id in [self.solution_set[event_id]['R'],self.solution_set[event_id2]]:
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
            self.solution_set[event_id1]['P']:self.solution_set[event_id2]['P'],
            self.solution_set[event_id2]['P']:self.solution_set[event_id1]['P']
        }

        moves=dict()
        kc.put(event_id1)
        while not kc.empty():
            current_event=kc.get()
            current_period=self.solution_set[current_event]['P']
            new_period=versus_periods[current_period]
            moves[current_event]=new_period
            eneighbors=self.problem.G.neioghbors(current_event)
            for neighbor in eneighbors:
                if neighbor in moves: continue
                if self.solution_set[neighbor]['P']==new_period:
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

    def select_operator(self):
        operator_choice=random.randint(1,3)

        if operator_choice==1:
            return self.transfer_event()
        elif operator_choice==2:
            return self.swap_events()
        elif operator_choice==3:
            return self.kempe_chain()
        else:
            raise ValueError(f"Operator {operator_choice} does not implement yet")

    def reposition(self,moves):
        self.memory.clear()
        move_cost=0
        for event_id,(period_id,room_id) in moves.items():
            self.memory[event_id]=(period_id,room_id)
            move_cost+=self.unschedule(event_id)
            move_cost+=self.schedule(event_id,room_id,period_id)
        
        return move_cost

    def rollback(self):
        for event_id,(period_id,room_id) in self.memory.items():
            self.unschedule(event_id)
            self.schedule(event_id,room_id,period_id)

if __name__=='__main__':
    pass


