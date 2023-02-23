from ast import Raise
from base import Problem,Core
from collections import defaultdict,Counter
import os,pickle,logging,pandas as pd,random
from ortools.sat.python import cp_model

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
        for sol_name in os.listdir(Core.path_to_solutions):
            if sol_name.startswith(self.solution_id) and sol_name.endswith('sln'):
                with open(os.path.join(Core.path_to_solutions,sol_name),'r') as RF:
                    for i,line in enumerate(RF):
                        period,room=[int(x) for x in line.split()]
                        if i in self.events_solution: 
                            self.unschedule(i)
                        self.schedule(i,period,room,init=i not in self.events_solution)
                return True
        return False
    
    def read_best(self):
        dataset_name=[x.strip() for x in os.listdir(os.path.join(Core.path_to_best_solutions)) if x.strip().startswith(self.solution_id.strip())]
        print(self.solution_id.strip(),dataset_name)
        if len(dataset_name)==0:
            return
        dataset_name=dataset_name[0]
        with open(os.path.join(Core.path_to_best_solutions,dataset_name),'r') as RF:
            for i,line in enumerate(RF):
                period_id,room_id=[int(x.strip()) for x in line.strip()]
                if i in self.events_solution:
                    self.unschedule(i)
                self.schedule(i,period_id,room_id,init=i not in self.events_solution)
    
    def pickle_sol(self):
        with open(os.path.join(Core.path_to_seriallize_init,self.solution_id+'.pcl'),'wb') as WF:
            pickle.dump(self.events_solution,WF)


    def save(self):
        arena_path=os.path.join(Core.path_to_solutions,'arena.xlsx')
        candicate_solution_cost=self.compute_cost()
        with open(os.path.join(Core.path_to_solutions,f'{self.solution_id}_{candicate_solution_cost}.sln'),'w') as WF:
            self.events_solution=dict(sorted(self.events_solution.items(),key=lambda x:x[0]))
            for _,(period,room) in self.events_solution.items():
                WF.write(f'{period} {room}\n')
        

        arenaDF=pd.read_excel(arena_path)
        arena_id=arenaDF.query('instance==@self.problem.id').index[0]
        if arenaDF.iloc[arena_id]['our_solution']>candicate_solution_cost:
            arenaDF.at[arena_id,'our_solution']=candicate_solution_cost

        arenaDF.to_excel(arena_path,index=False)
    
    def set_(self,solution_set,init=False):
        if len(solution_set)==0: 
            Raise(f"Invalid amount of solutions for:{self.solution_id}")
        for event_id,(period_id,room_id) in solution_set.items():
            if not init:
                self.unschedule(event_id)
            self.schedule(event_id,period_id,room_id,init)
    
        if init:
            self.cost=self.compute_cost()
    
    def compute_cost(self,verbose=False):
        if verbose:
            logger=logging.getLogger('cost_contributon')
            logger.setLevel(logging.INFO)
            formatter=logging.Formatter('%(asctime)s\t%(message)s')
            sh=logging.StreamHandler()
            sh.setFormatter(formatter)
            logger.addHandler(sh)

            isolated_events=0
            consecutive_events=0
            late_events=0

        cost_value=0
        for _,student_events in self.problem.students.items():
            student_periods=[self.events_solution[event_id][0] for event_id in student_events]
            events_per_day={}
            for period_id in student_periods:
                events_per_day[period_id//Core.periods_per_day]=events_per_day.get(period_id//Core.periods_per_day,0)+1
            for day,number_of_events in events_per_day.items():
                if number_of_events==1: 
                    cost_value+=1
                    if verbose:
                        isolated_events+=1
                
                elif number_of_events>2:
                    consecutive=0
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day):
                        if period_id in student_periods: 
                            consecutive+=1
                        else:
                            if consecutive>2:
                                cost_value+=(consecutive-2)
                                if verbose:
                                    consecutive_events+=(consecutive-2)
                            consecutive=0
                    if consecutive>2:
                        cost_value+=(consecutive-2)
                        if verbose:
                            consecutive_events+=(consecutive-2)
        
        for event_id,attributes in self.problem.events.items():
            if self.events_solution[event_id][0] in Core.last_periods_per_day:
                cost_value+=len(attributes['S'])
                if verbose:
                    late_events+=len(attributes['S'])

        if verbose:
            logger.info(f'Isolated Events:{isolated_events}')
            logger.info(f'Consecutive Events:{consecutive_events}')
            logger.info(f'Late Events:{late_events}')
        return cost_value
    
    def compute_day_cost(self,day):
        cost_value=0
        events_in_day=set()
        for _,student_events in self.problem.students.items():
            student_day_periods=[self.events_solution[event_id][0] for event_id in student_events if self.events_solution[event_id][0]//Core.periods_per_day==day]
            events_in_day=events_in_day.union(set(student_events))
            if len(student_day_periods)==0: continue
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
                if consecutive>2:
                    cost_value+=(consecutive-2)
        
        for event_id in events_in_day:
            if self.events_solution[event_id][0]==day*Core.periods_per_day+Core.periods_per_day-1:
                cost_value+=len(self.problem.events[event_id]['S'])

        return cost_value

    def schedule(self,event_id,period_id,room_id,init=False):
        if not init:
            current_day=period_id//Core.periods_per_day
            event_students=self.problem.events[event_id]['S']

            # Calculate how the period change will effect the current cost
            cost_distribution=0
            for student_id in event_students:
                student_periods=[self.events_solution[eid][0] for eid in self.problem.students[student_id]]

                events_in_days=Counter([self.events_solution[eid][0]//Core.periods_per_day for eid in self.problem.students[student_id]]) 
                if events_in_days.get(current_day,-1)==0:
                    cost_distribution+=1
                    continue
                elif events_in_days.get(current_day,-1)==1 and student_periods[0]!=period_id:
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
                if period_id not in student_periods:
                    student_periods.append(period_id)
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

    def feasibility(self):
        constraint_violations=0
        logger=logging.getLogger("Feasibility logger")
        logger.setLevel(logging.INFO)
        formatter=logging.Formatter('%(asctime)s\t%(message)s')
        sh=logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        for event_id in range(self.problem.E):
            for event_id2 in self.problem.G.neighbors(event_id):
                if event_id>event_id2: continue
                if self.events_solution[event_id][0]==self.events_solution[event_id2][0] and self.events_solution[event_id][1]==self.events_solution[event_id2][1]:
                    print(self.problem.event_rooms[event_id],self.problem.event_rooms[event_id2])
                    logger.info(f'Event {event_id} and event {event_id2} are conflicted in period:{self.events_solution[event_id][0]}')
                    constraint_violations+=1

            for event_id2 in self.problem.after_events[event_id]:
                if self.events_solution[event_id][0]>self.events_solution[event_id2][0]:
                    logger.info(f'Event {event_id} and event {event_id2} violate precedance relation')
                    constraint_violations+=1

        for room_id in self.problem.rooms.keys():
            periods_counter=Counter([self.events_solution[event_id] for event_id in self.roomwise_solution[event_id]])
            for period_id,occurences in periods_counter.items():
                if occurences>1:
                    logger.info(f'Placement violation in room {room_id} and period {period_id}')
                    constraint_violations+=1

        logger.info(f'Total constraints:{constraint_violations}')

    def can_be_moved(self,event_id,period_id,excluded=[]):
        for neighbor_event in list(self.problem.G.neighbors(event_id)):
            if neighbor_event in excluded: continue
            if period_id==self.events_solution[neighbor_event][0]:
                return False
        
        if self.problem.formulation=='full':
            for event_id2 in self.problem.after_events[event_id]:
                if event_id2 in excluded: continue
                if period_id<self.events_solution[event_id2][0]:
                    return False

        return True

    def room_period_availability(self,room_id,period_id,excluded=[]):
        for event_id in self.roomwise_solution[room_id]:
            if event_id in excluded: continue
            if period_id==self.events_solution[event_id][0]:
                return False
        return True
    
    def reposition(self,moves):
        for event_id,(period_id,room_id) in moves.items():
            self.unschedule(event_id)
            self.schedule(event_id,period_id,room_id)

    def get_move(self):
        random_move=random.randint(1,3)
        if random_move==1: 
            return self.transfer(),"TRANSFER EVENT"
        elif random_move==2:
            return self.swap_events(),"SWAP EVENTS"
        elif random_move==3:
            return self.kempe_chain(),"KEMPE CHAIN"
        else:
            Raise(f'Move_{random_move}: Not Implement yet')

    # --------- Operators ------------

    def transfer(self):
        event_id=random.randint(0,self.problem.E-1)
        period_id=random.randint(0,Core.P-1)
        while period_id==self.events_solution[event_id][0]:
            period_id=random.randint(0,Core.P-1)
        
        if self.can_be_moved(event_id,period_id): 
            if self.room_period_availability(self.events_solution[event_id][1],period_id):
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
            if not self.can_be_moved(current_event,new_period,excluded=[neighbor for neighbor in self.problem.G.neighbors(current_event) if self.events_solution[neighbor][0]==new_period]):
                return dict()
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
    
    def optimize_rooms(problem:Problem,eset=[],initial_solution={},time_limit=600):
        shints={student_id:{p:False for p in range(Core.P)} for student_id in problem.students.keys()}
        for student_id,student_events in problem.students.items():
                for eid in student_events:
                    if eid in eset: continue
                    shints[student_id][initial_solution[event_id][0]]=True

        model=cp_model.CpModel()
        xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'xvar_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in problem.rooms.keys() for period_id in range(problem.P)}
        
        if initial_solution: 
            for event_id,(period_id,room_id) in initial_solution.items():
                if event_id not in eset: continue
                model.AddHint(xvars[(event_id,room_id,period_id)],1)


        for event_id in eset:
            for room_id in range(problem.R):
                if room_id in problem.event_rooms[event_id]: continue
                model.Add(
                    sum([xvars[(event_id,room_id,period_id)] for period_id in range(Core.P)])==0
                )
            
            for period_id in range(Core.P):
                if period_id in problem.event_periods[event_id]:
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(Core.P)])==0
                    )

        for event_id in eset:
            model.Add(sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])==1)
        
        for room_id in range(problem.R):
            for period_id in range(Core.P):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in eset
                        ])<=1
                )
        
        for event_id in eset:
            for event_id2 in problem.G.neighbors(event_id):
                if event_id2 not in eset: 
                    model.Add(xvars[(event_id,initial_solution[event_id2][1],initial_solution[event_id2][0])] ==0)
                else:
                    for period_id in range(Core.P):
                        if period_id not in problem.event_periods[event_id] or period_id not in problem.event_periods[event_id2]: continue
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])
                            +sum([xvars[(event_id2,room_id,period_id)] for room_id in range(problem.R) for period_id in range(Core.P)])
                            <=1
                        )
        if problem.formulation=='full':
            for event_id in eset:
                for event_id2 in problem.after_events[event_id]:
                    if event_id2 not in eset:
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(Core.P)])<initial_solution[event_id][0]
                        )
                    else:
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(Core.P)])<
                            sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(Core.P)])
                        )

        event_students={student_id for event_id in eset for student_id in problem.events[event_id]['S']}
        single_events={(student_id,day):model.NewBoolVar(name=f'se_{student_id}_{day}') for student_id in event_students for day in range(Core.days)}
        consecutive={(student_id,day,i):[model.NewBoolVar(name=f'consecutive_{student_id}_{day}_{i}_0'),model.NewBoolVar(name=f'consecutive_{student_id}_{day}_{i}_1')] for student_id in event_students for day in range(Core.days) for i in range(3,5)}
        consecutive.update({(student_id,day,i):model.NewBoolVar(name=f'consecutive_{student_id}_{day}_{i}_0') for student_id in event_students for day in range(Core.days) for i in range(3,5)})
        for student_id in event_students:
            for day in range(Core.days):
                for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day):
                    model.Add(
                        -sum([xvars[(event_id,room_id,period_id)] for event_id in event_students for room_id in problem.rooms.keys()])
                        -shints[(student_id,period_id)]
                        +sum([xvars[(event_id,room_id,pcurrent)] for event_id in event_students for room_id in problem.rooms.keys() for pcurrent in [x for x in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day) if x!=period_id]])
                        +sum([shints[student_id][pid] for pid in [x for x in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day) if x!=period_id]])
                        +single_events[(student_id,day)]>=0
                    )
                
                for i in range(3,5):
                    threshold=Core.periods_per_day-(i*2)    
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-i+1):
                        previous_period=period_id-1
                        next_period=period_id+i
                        previous_cost_contribution=sum([xvars[(event_id,room_id,previous_period)] for event_id in eset for room_id in problem.rooms.keys()])+shints[student_id][previous_period] if not previous_period<day*Core.periods_per_day else 0
                        next_cost_contribution=sum([xvars[(event_id,room_id,next_period)] for event_id in eset for room_id in problem.rooms.keys()])+shints[student_id][next_period] if not next_period>day*Core.periods_per_day+Core.periods_per_day else 0
                        model.Add(
                            previous_cost_contribution
                            -sum([xvars[(event_id,room_id,period_id)] 
                                for event_id in eset
                                for room_id in problem.rooms.keys()
                                for period_id in range(period_id,next_period)
                            ])
                            +next_cost_contribution
                            +consecutive[(student_id,day,i)][0]
                            >=-(i-1)
                        )
                        if period_id<threshold:
                            for pid in range(next_period+1,day*Core.periods_per_day+Core.periods_per_day-i+1):
                                previous_period=pid-1
                                next_period2=pid+i
                                next_cost_contribution=sum([xvars[(event_id,room_id,next_period2)] for event_id in eset for room_id in problem.rooms.keys()])+shints[student_id][next_period2] if not next_period2>day*Core.periods_per_day+Core.periods_per_day else 0

                                model.Add(
                                    sum([xvars[(event_id,room_id,previous_period)] for event_id in eset for room_id in problem.rooms.keys()])+shints[student_id][previous_period]
                                    -sum([xvars[(event_id,room_id,pcurr)] for event_id in eset for room_id in problem.rooms.keys() for pcurr in range(pid,next_period2)])
                                    +next_cost_contribution
                                    +consecutive[(student_id,day,i)][1]
                                    >=-(i-1)
                                ).OnlyEnforceIf(consecutive[(student_id,day,i)][0])
                
                for i in range(5,Core.periods_per_day):
                    for period_id in range(day*Core.periods_per_day,day*Core.periods_per_day+Core.periods_per_day-i+1):
                        previous_period=period_id-1
                        next_period=period_id+i
                        
                        previous_cost_contribution=sum([xvars[(event_id,room_id,previous_period)] for event_id in eset for room_id in problem.rooms.keys()])+shints[student_id][previous_period] if previous_period>=day*Core.periods_per_day else 0
                        next_cost_contribution=sum([xvars[(event_id,room_id,next_period)] for event_id in eset for room_id in problem.rooms.keys()])+shints[student_id][next_period] if next_period<=day*Core.periods_per_day+Core.periods_per_day-1 else 0
                        model.Add(
                            previous_cost_contribution
                            -sum([
                                xvars[(event_id,room_id,pid)]
                                for event_id in eset
                                for room_id in range(problem.R)
                                for pid in range(period_id,next_period)
                            ])
                            -sum([shints[student_id][pid]  for pid in range(period_id,next_period)])
                            +next_cost_contribution
                            +consecutive[(student_id,day,i)]
                            >=-(i-1)
                        )
        
        objective=[
            sum([single_events[(student_id,day)] for student_id in event_students for day in  range(Core.days)]),
            sum([consecutive[(student_id,day,i)][j] * (i-2) for student_id in event_students for day in range(Core.days) for i in range(3,5) for j in [0,1]]),
            sum([consecutive[(student_id,day,i)] * (i-2) for student_id in event_students for day in range(Core.days) for i in range(5,Core.periods_per_day)]),
            sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R) for period_id in Core.last_periods_per_day])
        ]

        model.Minimize(sum(objective))
        solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = os.cpu_count()
        solver.parameters.log_search_progress=True
        status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
        esol={}
        if status==cp_model.OPTIMAL or status==cp_model.FEASIBLE:
            for (event_id,room_id,period_id),dvar in xvars.items():
                if solver.Value(dvar)==1:
                    esol[event_id]=(period_id,room_id)
        return esol