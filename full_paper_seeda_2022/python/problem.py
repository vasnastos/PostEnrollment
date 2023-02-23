from ast import Raise
import os,networkx as nx
from collections import defaultdict,Counter
from tabulate import tabulate
import logging,pandas as pd
from itertools import combinations
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
from time import time
import math

class Core:
    P=45
    days=5
    periods_per_day=9
    path_to_instances=os.path.join('','instances')
    path_to_solutions=os.path.join('','solutions')
    path_to_initial_solutions=os.path.join('','solutions','init')
    ps_datasets=pd.read_excel(os.path.join('','instances','pe-ctt.xlsx'))
    big_instances=[ds for ds in os.listdir(os.path.join(os.path.join('','instances'))) if ds.startswith('big')]
    easy_instances=[ds for ds in os.listdir(os.path.join(os.path.join('','instances'))) if ds.startswith('easy')]
    itc_2002_instances=[ds for ds in os.listdir(os.path.join(os.path.join('','instances'))) if ds.startswith('o')]
    itc_2007_instances=[ds for ds in os.listdir(os.path.join(os.path.join('','instances'))) if ds.startswith('i')]
    small_instances=[ds for ds in os.listdir(os.path.join(os.path.join('','instances'))) if ds.startswith('small')]
    medium_instances=[ds for ds in os.listdir(os.path.join(os.path.join('','instances'))) if ds.startswith('medium')]
    last_periods_per_day=[day*9+8 for day in range(days)]
    zero_cost_instances=['o20.tim','i01.tim','i02.tim','i05.tim','i06.tim','i07.tim','i08.tim','i09.tim','i10.tim','i12.tim','i13.tim','i14.tim','i15.tim','i16.tim','i17.tim','i18.tim','i19.tim','i24.tim']

    @staticmethod
    def formulation(ds_name):
        return Core.ps_datasets.query('instance==@ds_name')['formulation'].to_list()[0]

    @staticmethod
    def datasets(partial=[],all=False):
        if len(partial)!=0 and all:
            Raise("You select partial datasets among with all datasets")
        if all:
            return [x for x in os.listdir(Core.path_to_datasets) if x.endswith('.tim')]
        else:
            merged_datasets=[]
            for instance_team in partial:
                if instance_team=='easy':
                    merged_datasets.extend(Core.easy_instances)
                elif instance_team=='small':
                    merged_datasets.extend(Core.small_instances)    
                elif instance_team=='medium':
                    merged_datasets.extend(Core.medium_instances)
                elif instance_team=='itc_2002':
                    merged_datasets.extend(Core.itc_2002_instances)
                elif instance_team=='itc_2007':
                    merged_datasets.extend(Core.itc_2007_instances)
                elif instance_team=='big':
                    merged_datasets.extend(Core.big_instances)
                else:
                    Raise(f'Option:{instance_team} unavailable: Select one of the following[easy, small, medium,itc_2002, itc_2007, big]')

            return merged_datasets

class Problem:
    def __init__(self):
        self.events=dict()
        self.rooms=dict()
        self.students=defaultdict(list)
        self.event_rooms=defaultdict(list)
        self.event_periods=defaultdict(list)
        self.after_events=defaultdict(list)
        self.G=nx.Graph()
        self.event_combinations=dict()
        self.formulation=None
        self.event_combinations=dict()
    
    def reset(self):
        self.events.clear()
        self.rooms.clear()
        self.students.clear()
        self.event_rooms.clear()
        self.event_periods.clear()
        self.after_events.clear()
        self.G.clear()
        self.event_combinations.clear()
        self.formulation=None
    
    def read_instance(self,ds_name):
        self.reset()
        self.formulation=Core.formulation(ds_name).strip()
        with open(os.path.join(Core.path_to_instances,ds_name),'r') as RF:
            line=RF.readline()
            self.E,self.R,self.F,self.S=[int(x.strip()) for x in line.split()]
            self.events={e:{'S':set(),'F':set()} for e in range(self.E)}
            self.event_periods={e:list(range(Core.P)) for e in range(self.E)}
            self.rooms={r:{'C':-1,'F':set()} for r in range(self.R)}

            for r in range(self.R):
                line=RF.readline()
                self.rooms[r]['C']=int(line)

            for s in  range(self.S):
                for e in range(self.E):
                    line=RF.readline()
                    if int(line)==1:
                        self.events[e]['S'].add(s)
                        self.students[s].append(e)
            
            for r in range(self.R):
                for f in range(self.F):
                    line=RF.readline()
                    if int(line)==1:
                        self.rooms[r]['F'].add(f)
            
            for e in range(self.E):
                for f in range(self.F):
                    line=RF.readline()
                    if int(line)==1:
                        self.events[e]['F'].add(f)
            
            if self.formulation=='full':
                for e in range(self.E):
                    for p in range(Core.P):
                        line=RF.readline()
                        if int(line)==0:
                            self.event_periods[e].remove(p)

                for e in range(self.E):
                    for e2 in range(self.E):
                        line=RF.readline()
                        if e==e2: continue
                        if int(line)==1:
                            self.after_events[e].append(e2)
                        elif int(line)==-1:
                            self.after_events[e2].append(e)

        for e in range(self.E):
            for r in range(self.R):
                if self.events[e]['F'].issubset(self.rooms[r]['F']) and len(self.events[e]['S'])<=self.rooms[r]['C']:
                    self.event_rooms[e].append(r)
        
        self.G.add_nodes_from(list(range(self.E)))
        for e in range(self.E):
            for e2 in range(e+1,self.E):
                cs=len(self.events[e]['S'].intersection(self.events[e2]['S']))
                if cs>0:
                    self.G.add_edge(e,e2,weight=cs)
                elif self.event_rooms[e]==self.event_rooms[e2] and len(self.event_rooms[e])==1:
                    self.G.add_edge(e,e2,weight=1)
        
        # Find event combinations of 3
        for events in self.students.values():
            for combination in combinations(events,3):
                self.event_combinations[frozenset(combination)] =  self.event_combinations.get(frozenset(combination),0)+1
        
    def identical_students(self,verbose=False):
        logger=logging.getLogger("identical_events_logger")
        formatter=logging.Formatter('%(asctime)s\t%(message)s')
        sh=logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        identical_students=dict()
        student_in_use={student_id:False for student_id in self.students}
        for student_id in range(self.S):
            if student_in_use[student_id]: continue
            for student_id2 in range(student_id+1,self.S):
                if student_in_use[student_id2]: continue
                if self.students[student_id]==self.students[student_id2]:
                    student_in_use[student_id] = True
                    if (student_id,tuple(self.students[student_id])) not in identical_students:
                        identical_students[(student_id,tuple(self.students[student_id]))]=list()
                    identical_students[(student_id,tuple(self.students[student_id]))].append(student_id2)
                    student_in_use[student_id2]=True
            if student_in_use[student_id]:
                logger.debug(f'Identicals students[{student_id}]: {", ".join([str(student_id2) for student_id2 in identical_students[(student_id,tuple(self.students[student_id]))]])}')
        logger.debug(f'Total identical student relations:{len(identical_students.keys())}')
        del student_in_use
        return identical_students

    def room_combinations(self):
        drooms={}
        for event_id,rooms in self.event_rooms.items():
            if frozenset(rooms) not in drooms:
                drooms[frozenset(rooms)]=list()
            drooms[frozenset(rooms)].append(event_id)
        return drooms
    
    def __str__(self):
        return f"""
            {self.E=}\n
            {self.F=}\n
            {self.R=}\n
            {self.S=}\n
        """
    
class Solution:
    def __init__(self,ds_name:str):
        self.problem=Problem()
        self.problem.read_instance(ds_name)
        self.solution_id=ds_name.replace('.tim','')
        self.events_solution=dict()
        self.roomwise_solution=defaultdict(list)
        self.periodwise_solution=defaultdict(list)
        self.cost=0

    def read(self):
        with open(os.path.join(Core.path_to_solutions,f'{self.solution_id}.sol'),'r') as RF:
            for i,line in enumerate(RF):
                period,room=[int(x) for x in line.split()]
                if i in self.events_solution: 
                    self.unschedule(i)
                self.schedule(i,period,room)
    
    def save(self):
        with open(os.path.join(Core.path_to_solutions,f'{self.solution_id}_{self.compute_cost()}.sol'),'w') as WF:
            for i,(period,room) in self.events_solution.items():
                WF.write(f'{period} {room}\n')
    
    def set_(self,solution_set,init=False):
        if len(solution_set)==0: 
            Raise(f"Invalid amount of solutions for:{self.solution_id}")
        for event_id,(period_id,room_id) in solution_set.items():
            if not init:
                self.unschedule(event_id)
            self.schedule(event_id,period_id,room_id,init)
    
        if init:
            self.cost=self.compute_cost()


    def compute_cost(self):
        cost_value=0
        for _,student_events in self.problem.students.items():
            student_periods=[self.events_solution[event_id][0] for event_id in student_events]
            events_per_day=Counter([period_id//Core.periods_per_day for period_id in student_periods])
            for day,number_of_events in events_per_day.items():
                if number_of_events==1: 
                    cost_value+=1
                
                if number_of_events>2:
                    consecutive=0
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day):
                        if period_id in student_periods: 
                            consecutive+=1
                        else:
                            if consecutive>2:
                                cost_value+=(consecutive-2)
                            consecutive=0
        
        for event_id,attributes in self.problem.events.items():
            if self.events_solution[event_id][0] in Core.last_periods_per_day:
                cost_value+=len(attributes['S'])

        return cost_value
    
    def compute_day_cost(self,day):
        cost_value=0
        for _,student_events in self.problem.students.items():
            student_day_periods=[self.events_solution[event_id][0] for event_id in student_events if self.events_solution[event_id][0]//Core.periods_per_day==day]
            student_day_periods=list(sorted(student_day_periods))
            if len(student_day_periods)==0: continue
            for event_id in student_events:
                if self.events_solution[event_id][0]==day*Core.periods_per_day+Core.periods_per_day-1:
                    cost_value+=len(self.problem.events[event_id]['S'])

            if len(student_day_periods)==1: 
                cost_value+=1
            elif len(student_day_periods)==2: 
                continue
            else:
                consecutive=0
                for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day):
                    if period_id in student_day_periods: 
                        consecutive+=1
                    else:
                        if consecutive>2:
                            cost_value+=(consecutive-2)
                        consecutive=0    
        return cost_value

    def schedule(self,event_id,period_id,room_id,init=False):
        if not init:
            current_day=period_id//Core.periods_per_day
            event_students=self.problem.events[event_id]['S']

            # Calculate how the period change will effect the current cost
            cost_distribution=0
            for student_id in event_students:
                student_periods={self.events_solution[eid][0] for eid in self.problem.students[student_id]}

                events_in_days=Counter([self.events_solution[eid][0]//Core.periods_per_day for eid in self.problem.students[student_id]]) 
                if events_in_days.get(current_day,0):
                    cost_distribution+=1
                    continue
                elif events_in_days[current_day]==1 and student_periods[0]!=period_id:
                    cost_distribution-=1
                    continue

                # 1. Calculate previous consecutive cost effect
                consecutive=0
                for pid in range(current_day*Core.periods_per_day,current_day*Core.periods_per_day+Core.periods_per_day):
                    if pid in student_periods:
                        consecutive+=1
                    else:
                        if consecutive>2:
                            cost_distribution-=(consecutive-2)
                        consecutive=0

                # 2. Calculating current consecutive cost effect
                consecutive=0
                student_periods.add(period_id)
                for pid in range(current_day*Core.periods_per_day,current_day*Core.periods_per_day+Core.periods_per_day):
                    if pid in student_periods:
                        consecutive+=1
                    else:
                        if consecutive>2:
                            cost_distribution+=(consecutive-2)
                        consecutive=0
            if period_id==current_day*Core.periods_per_day+Core.periods_per_day-1:
                cost_distribution+=len(self.problem.events[event_id]['S'])            

            self.cost+=cost_distribution

        self.periodwise_solution[period_id].append(event_id)
        self.roomwise_solution[room_id].append(event_id)
        self.events_solution[event_id]=(period_id,room_id)
        

    
    def unschedule(self,event_id):
        cost_distribution=0
        current_day=self.events_solution[event_id][0]//Core.periods_per_day
        for student_id in self.problem.events[event_id]['S']:
            student_periods=[self.events_solution[eid][0] for eid in self.problem.students[student_id]]
            events_per_day=Counter([period_id//Core.periods_per_day for period_id in student_periods])
            if events_per_day[current_day]==1:
                cost_distribution-=1
                continue
            elif events_per_day[current_day]==2:
                cost_distribution+=1
                continue
            
            consecutive=0
            for period_id in range(current_day*Core.periods_per_day,current_day*Core.periods_per_day+Core.periods_per_day):
                if period_id in student_periods: 
                    consecutive+=1
                else:
                    if consecutive>2:
                        cost_distribution-=(consecutive-2)
                    consecutive=0
            
            student_periods.remove(self.events_solution[event_id][0])
            consecutive=0
            for period_id in range(current_day*Core.periods_per_day+Core.periods_per_day):
                if period_id in student_periods:
                    consecutive+=1
                else:
                    if consecutive>2:
                        cost_distribution+=(consecutive-2)
                    consecutive=0
        if self.events_solution[event_id][0]==current_day*Core.periods_per_day+Core.periods_per_day-1:
            cost_distribution-=len(self.problem.events[event_id]['S'])

        self.cost+=cost_distribution
        self.periodwise_solution[self.events_solution[event_id][0]].remove(event_id)
        self.roomwise_solution[self.events_solution[event_id][1]].remove(event_id)
        self.events_solution[event_id]=(-1,-1)

    def can_be_moved(self,event_id,period_id,excluded=[]):
        for neighbor_event in list(self.problem.G.neighbors(event_id)):
            if neighbor_event in excluded: continue
            if period_id==self.events_solution[neighbor_event][0]:
                return False
        return True

    def room_period_availability(self,room_id,period_id,excluded=[]):
        for event_id in self.roomwise_solution[room_id]:
            if event_id in excluded: continue
            if period_id==self.events_solution[event_id][0]:
                return False
        return True

    def transfer(self):
        event_id=random.randint(0,self.problem.E-1)
        period_id=random.randint(0,Core.P-1)
        while period_id==self.events_solution[event_id][0]:
            period_id=random.randint(0,Core.P-1)
        
        if self.can_be_moved(event_id,period_id) and self.room_period_availability(self.events_solution[event_id][1],period_id):
            return {
                event_id:(period_id,self.events_solution[event_id][1])
            }
        else:
            for room_id in self.problem.event_rooms[event_id]:
                if room_id==self.events_solution[event_id][1]: continue
                if self.room_period_availability(room_id,period_id):
                    return {
                        event_id:(period_id,room_id)
                    }
        return dict()
    
    def swap_events(self):
        event1_id=random.randint(0,self.problem.E-1)
        while len(list(self.problem.G.neighbors(event1_id)))==0:
            event1_id=random.randint(0,self.problem.E-1)
        event2_id=list(self.problem.G.neighbors(event1_id))[random.randint(0,len(list(self.problem.G.neighbors(event1_id)))-1)]

        if self.can_be_moved(event1_id,self.events_solution[event2_id][0],excluded=[event2_id]) and self.can_be_moved(event2_id,self.events_solution[event1_id][0],excluded=[event1_id]):
            if self.room_period_availability(self.events_solution[event1_id][1],self.events_solution[event2_id][0],excluded=[event2_id]) and self.room_period_availability(self.events_solution[event2_id][1],self.events_solution[event1_id][0],excluded=[event1_id]):
               return {
                    event1_id:(self.events_solution[event2_id][0],self.events_solution[event1_id][1]),
                    event2_id:(self.events_solution[event1_id][0],self.events_solution[event2_id][1])
                }
            
            elif self.events_solution[event2_id][1] in self.problem.event_rooms[event1_id] and self.events_solution[event1_id][1] in self.problem.event_rooms[event2_id]:
                return {
                    event1_id:(self.events_solution[event2_id][0],self.events_solution[event2_id][1]),
                    event2_id:(self.events_solution[event1_id][0],self.events_solution[event1_id][1])
                }
            
            else:
                moves=dict()
                for room_id in self.problem.event_rooms[event1_id]:
                    if room_id==self.events_solution[event1_id][1]: continue
                    if self.room_period_availability(room_id,self.events_solution[event2_id][0]):
                        moves[event1_id]=(self.events_solution[event2_id][0],room_id)
                        break

                for room_id in self.problem.event_rooms[event2_id]:
                    if room_id==self.events_solution[event2_id][1]: continue
                    if self.room_period_availability(room_id,self.events_solution[event1_id][0]):
                        moves[event2_id]=(self.events_solution[event1_id][0],room_id)
                        break
                
                if len(moves)==2: 
                    return moves
                    
        return dict()
    
    def kempe_chain(self):
        from queue import LifoQueue
        event1_id=random.randint(0,self.problem.E-1)
        while len(list(self.problem.G.neighbors(event1_id)))==0:
            event1_id=random.randint(0,self.problem.E-1)
        neighbor_indeces=set()
        neighbor_events=list(self.problem.G.neighbors(event1_id))
        random_index=random.randint(0,len(neighbor_events)-1)
        event2_id=neighbor_events[random_index]
        neighbor_indeces.add(random_index)
        while self.events_solution[event1_id][0]//Core.periods_per_day==self.events_solution[event2_id][0]//Core.periods_per_day:
            random_index=random.randint(0,len(neighbor_events)-1)
            neighbor_indeces.add(random_index)
            if len(neighbor_indeces)==len(neighbor_events):
                break
            event2_id=neighbor_events[random_index]

        if len(neighbor_indeces)==len(neighbor_events):
            return dict()
        del neighbor_indeces

        kc=LifoQueue()
        kc.put(event1_id)
        versus_periods={
            self.events_solution[event1_id][0]:self.events_solution[event2_id][0],
            self.events_solution[event2_id][0]:self.events_solution[event1_id][0]
        }
        moves=dict()

        while not kc.empty():
            current_event=kc.get()
            current_period=self.events_solution[current_event][0]
            new_period=versus_periods[current_period]
            moves[current_event]=new_period
            for neighbor in self.problem.G.neighbors(current_event):
                if neighbor in moves: continue
                if self.events_solution[neighbor][0]==new_period:
                    kc.put(neighbor)
        
        if len(moves)==0: 
            return dict()

        final_moves_set=dict()
        for event_id,period_id in moves.items():
            if self.room_period_availability(self.events_solution[event_id][1],period_id):
                final_moves_set[event_id]=(period_id,self.events_solution[event_id][1])
            else:
                unset_rooms=True
                for room_id in self.problem.event_rooms[event_id]:
                    if room_id==self.events_solution[event_id][1]: continue
                    if self.room_period_availability(room_id,period_id):
                        final_moves_set[event_id]=(period_id,room_id)
                        unset_rooms=False
                        break
                
                if unset_rooms:
                    return dict()
        
        return final_moves_set

    def reposition(self,moves):
        for event_id,(period_id,room_id) in moves.items():
            self.unschedule(event_id)
            self.schedule(event_id,period_id,room_id)

    def get_move(self):
        random_move=random.randint(1,3)
        if random_move==1: 
            return self.transfer()
        elif random_move==2:
            return self.swap_events()
        elif random_move==3:
            return self.kempe_chain()
        else:
            Raise(f'Move_{random_move}: Not Implement yet')