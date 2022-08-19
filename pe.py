import os 
from collections import defaultdict,Counter
import networkx as nx
from tabulate import tabulate
import random
from queue import LifoQueue
from ortools.sat.python import cp_model
import docplex.cp.model as cpx

# Define vars
P=45
D=5
PPD=9


class Problem:
    _instances=os.path.join('','incstances')
    _solutions=os.path.join('','solutions')
    def __init__(self,ds_name):
        self.formulation=''
        self.name=ds_name
        self.students=defaultdict(list)
        self.rooms=defaultdict(dict)
        self.event_rooms=defaultdict(list)
        self.last_period_per_day=[d*PPD+PPD-1 for d in range(D)]

        RF=open(os.path.join(Problem._instances,ds_name))

        # First line==> Events Rooms Features Students
        line=RF.readline()
        self.E,self.R,self.F,self.S=[int(x) for x in line.split()]
        self.events={e:{"S":set(),"NE":list(),"F":set(),"P":list(range(P))} for e in range(self.E)}
        # Capacity of each room
        for i in range(self.R):
            self.rooms[i]['C']=int(RF.readline())

        # Event participation per  student
        for student_id in range(self.S):
            for i in range(self.E):
                line=RF.readline()
                if int(line)==1:
                    self.events[i]['S'].add(student_id)
                    self.students[i].append(i)
        
        # Features per room
        for r in range(self.R):
            self.rooms[r]['F']=set()
            for f in range(self.F):
                line=int(RF.readline())
                if int(line)==1:
                    self.rooms[r]['F'].add(f)
        
        # Features per event
        for e in range(self.E):
            for f in range(self.F):
                line=RF.readline()
                if int(line)==1:
                    self.events[e]['F'].add(e)
        

        if self.formulation=='':
            for e in range(self.E):
                for p in range(P):
                    line=RF.readline()
                    if int(line)==0:
                        self.events[e].remove(p)
            
            for eid1 in range(self.E):
                for eid2 in range(self.E):
                    line=RF.readline()
                    if line=="": break
                    if int(line)==1:
                        self.events[eid1]['NE'].append(eid2)
                    elif int(line)==-1:
                        self.events[eid2]['NE'].append(eid1)
    
        RF.close()

        for e in self.events.keys():
            for r in self.rooms.keys():
                if self.events[e]['F'].issubset(self.rooms[r]['F']):
                    self.event_rooms[e].append(r)

        self.G=nx.Graph()
        self.G.add_nodes_from(list(range(self.E)))
        for e in range(self.E):
            for e2 in range(1,self.E):
                cs=len(self.events[e]['S'].intersection(self.events[e2]['S']))
                if cs>0:
                    self.G.add_edge(e,e2,weight=cs)
                elif len(self.event_rooms[e])==len(self.event_rooms[e2])==1 and self.event_rooms[e]==self.event_rooms[e2]:
                    self.G.add_edge(e,e2,weight=1)
    
    def identical_students(self):
        ident_students=dict()
        student_temp_list=list(range(self.S))
        for student_id in student_temp_list:
            for student_id2 in student_temp_list:
                if student_id==student_id2: continue
                if self.students[student_id]==self.students[student_id2]:
                    if tuple(self.students[student_id]) not in ident_students:
                        ident_students[tuple(self.students[student_id])]=list()
                    if student_id not in ident_students[tuple(self.students[student_id])]:
                        ident_students[tuple(self.students[student_id])].append(student_id)
                    ident_students[tuple(self.students[student_id])].append(student_id2)
            
            for sid in ident_students[tuple(self.students[student_id])]:
                student_temp_list.remove(sid)
                
        return ident_students
    
    def room_suitability(self):
        return sum([len(self.event_rooms[eid]) for eid in range(self.E)])/self.E
    
    def room_size(self):
        return sum([self.rooms[r]['C'] for r in range(self.R)])/self.R
    
    def period_unavailability(self):
        if self.formulation=='':
            return 0
        return sum([P-len(self.events[e]['P']) for e in range(self.E)])/(self.E*P)
    
    def conflict_density(self):
        return (self.G.number_of_edges()*2)/(self.E**2)
    
    def precedence(self):
        return sum([len(self.events[e]['PE']) for e in range(self.E)])/self.E if self.formulatios=="" else 0
    
    def statistics(self):
        rows=[
            ['Id',self.name],
            ['Problem',self.origin],
            ['Events',self.E],
            ['Rooms',self.R],
            ['Students',self.S],
            ['Features',self.F],
            ['Precedence',self.precedence()],
            ['Conflict_density',self.conflict_density()],
            ['Percedence density',self.precedence_density()],
            ['Room suitability',self.room_suitability()],
            ['Average room size',self.room_size()],
            ['Average event period unavailability',self.period_unavailability()]
        ]
        return tabulate(rows,headers=['Statistic name','Value'],tablefmt='fancy_grid')
    
    def save_statistics(self):
        with open(os.path.join('','statistics.csv'),'w') as WF:
            WF.write(f'Id,{self.name}\n')
            WF.write(f'Problem,{self.origin}\n')
            WF.write(f'Events,{self.E}\n')
            WF.write(f'Rooms,{self.R}\n')
            WF.write(f'Students,{self.S}')
            WF.write(f'Features,{self.F}\n')
            WF.write(f'Precedence,{self.precedence()}\n')
            WF.write(f'Conflict_density,{self.conflict_density()}\n')
            WF.write(f'Percedence density,{self.precedence_density()}\n')
            WF.write(f'Room suitability,{self.room_suitability()}\n')
            WF.write(f'Average room size,{self.room_size()}\n')
            WF.write(f'Average event period unavailability,{self.period_unavailability()}\n')


class Solution:
    def __init__(self,ds_name):
        self.solution_id=ds_name.replace('.tim','')
        self.problem=Problem(ds_name)
        self.psolution=dict()
        self.rsolution=dict()
        self.tsolution=dict()
        self.periods=defaultdict(list)
        self.rooms=defaultdict(list)

    def schedule(self,e,p):
        self.psolution[e]=p
        self.periods[p].append(e)
    
    def unschedule(self,e):
        self.periods[self.psolution[e]].remove(e)
        self.psolution[e]=-1
    
    def place(self,e,r):
        self.rsolution[e]=r
        self.rooms[r].append(e)
    
    def uplace(self,e):
        self.rooms[self.rsolution[e]].remove(e)
        self.rsolution[e]=-1

    def set_solution(self,slndict):
        self.dsolution=slndict
        for e,(r,p) in self.tsolution.items():
            self.psolution[e]=p
            self.rsolution[e]=r
    
    def save_solution(self):
        with open(os.path.join('','solutions',f'{self.solution_id}.sol'),'w') as WF:
            self.tsolution=dict(sorted(self.tsolution.items(),key=lambda sol:sol[0]))
            for _,(r,p) in self.tsolution.items():
                WF.write(f'{r} {p}\n')
    
    def cost_variation(self,e,p):
        c=0
        old_period=self.psolution[e]
        old_day=old_period//PPD

        # Old cost
        for student_id in self.events[e]['S']:
            event_periods={self.psolution[e] for e in self.problem.students[student_id]}

            day_events=len([p for p in event_periods if p//PPD==old_day])

            if day_events==1:
                c-=1
            elif day_events==2:
                c+=1
            
            
            consecutive=0
            for p in range(old_day*PPD,old_day*PPD+PPD):
                if p in event_periods:
                    consecutive+=1
                else:
                    if consecutive>2:
                        c-=consecutive-2
                    consecutive=0

            event_periods.remove(old_period)
            # Check for old_day variation
            consecutive=0
            for p in range(old_day*PPD,old_day*PPD+PPD):
                if p in event_periods:
                    consecutive+=1
                else:
                    if consecutive>2:
                        c+=consecutive-2
                    consecutive=0

            new_day=p//PPD
            day_events=len([p1 for p1 in event_periods if p1//PPD==new_day])
            if day_events==0:
                c+=1
            elif day_events==1:
                c-=1
            
            
            consecutive=0
            for pid in range(new_day*PPD,new_day*PPD+PPD):
                if pid in event_periods:
                    consecutive+=1
                else:
                    if consecutive>2:
                        c-=consecutive-2
            


            event_periods.append(p)
            daily_events=len([p1 for p1 in event_periods if p1//PPD==new_day])
            if daily_events==1:
                c+=1

            for pid in range(new_day*PPD,new_day*PPD+PPD):
                if pid in event_periods: 
                    consecutive+=1
                else:
                    if consecutive>2:
                        c+=consecutive-2
            
        if old_period in self.problem.last_period_per_day:
                c-=len(self.problem.events[e]['S'])
        if p in self.problem.last_period_per_day:
                c+=len(self.problem.events[e]['S'])

        return c

    def compute_cost(self):
        c=0
        for _,student_events in self.problem.students:
            event_periods={self.psolution[e] for e in student_events}

            # sinngle events
            courses_per_day=Counter([x//PPD for x in event_periods])
            for d in range(D):
                if courses_per_day[d]==1:
                    c+=1
            
            # consecutive events
            for d in range(D):
                consecutive=0
                for p in range(d*PPD,d*PPD+PPD):
                    if p in event_periods:
                        consecutive+=1
                    else:
                        if consecutive>2:
                            c+=consecutive-2 
                        consecutive=0
        
        # last day-timeslot events
        c+=sum([len(self.problem.events[e]['S']) for e in range(self.problem.E) if self.psolution[e] in self.problem.last_period_per_day])
        
        return c

    # --------------- Neighborhood operators ----------------
    def create_solution_hints(self,eset):
        rhints={rid:{pid:False for pid in range(P)} for rid in range(self.problem.R)}
        for e in range(self.problem.E):
            if e in eset: continue
            rhints[self.rsolution[e]][self.psolution[e]]=True
        return rhints
    
    def create_student_hints(self,students_list=[]):
        if students_list==[]:
            students_list=list(range(self.problem.S))
        shints={student_id:{pid:False for pid in range(P)} for student_id in students_list}
        for student_id in students_list:
            for e in self.problem.students[student_id]:
                shints[student_id][self.psolution[e]]=True
        return shints
    
    def create_event_hints(self,exclude_events=[]):
        ehints={e:{p:False for p in range(P)} for e in range(self.problem.E)}
        for e,p in self.psolution.items():
            if e in exclude_events: continue
            ehints[e][p]=True
        return ehints

    def find_room_sol(self,eset):
        model=cp_model.CpModel()
        dparams={e:model.NewIntVar(0,self.problem.R-1,name=f'room_selection_{e}') for e in eset}
        rooms_to_integer=list(self.problem.rooms.keys())

        for e in eset:
            for i in range(self.problem.R):
                if rooms_to_integer[i] not in self.problem.event_rooms[e]:
                    model.Add(dparams[e]!=i)
            for e2 in self.periods[self.psolution[e]]:
                if e2 in eset:
                    model.Add(dparams[e]!=dparams[e2])
                else:
                    model.Add(dparams[e]!=self.rsolution[e])
        
        solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds=100
        solver.parameters.num_search_workers=os.cpu_count()
        status=solver.Solve(model)
        if status==cp_model.FEASIBLE or status==cp_model.OPTIMAL:
            return {e:rooms_to_integer[solver.Value(dv)] for e,dv in dparams.items()}
        return {}
    
    def optimize_room_status(self,rid:int):
        hints=self.create_solution_hints()
        model=cpx.CpoModel()
        rparams={(e,r,p):model.binary_var(name=f'room_decision_variable_{e}_{r}_{p}') for e in self.rooms[rid] for r in self.problem.event_rooms[e] for p in self.problem.events[e]['P']}

        for e in self.rooms[rid]:
            model.add(sum([rparams[(e,r,p)] for r in self.problem.event_rooms[e] for p in self.problem.events[e]['P']])==1)
        
        for rid in self.problem.rooms.keys():
            for pid in range(P):
                model.Add(sum([rparams[(e,rid,pid)] for e in self.rooms[rid]])+hints[rid][pid]<=1)
        
        for e in self.rooms[rid]:
            for e2 in self.problem.G.neighbors(e):
                for pid in range(P):
                    if pid not in self.problem.events[e]['P'] or pid not in self.problem.events[e2]['P']: continue    
                    if e2 in self.rooms[rid]:
                        model.add(sum([rparams[(e,rid,pid)] for rid in self.problem.event_rooms[e]])+sum([rparams[(e2,rid,pid)] for rid in self.problem.event_rooms[e2]])<=1)
        
        event_students={sid for e in self.rooms[rid] for sid in self.problem.events[e]['S']}
        shints=self.create_student_hints(event_students)
        single_day_events={(student_id,d):model.binary_var(name=f'single_day_event_{student_id}_{d}') for student_id in event_students for d in range(D)}
        consecutive_events={(student_id,d,i):[model.binary_var(name=f'consecutive_event_{student_id}_{d}_{i}_0'),model.binary_var(name=f'consecutive_event_{student_id}_{d}_{i}_1')] for student_id in event_students for d in range(D) for i in range(3,5)}
        consecutive_events.update({(student_id,d,i):model.binary_var(name=f'consecutive_event_{student_id}_{d}_{i}') for student_id in event_students for d in range(D) for i in range(5,PPD+1)})

        for student_id in event_students:
            suitable_events=list(set(self.problem.students[student_id]).intersection(set(self.rooms[rid])))
            for d in range(D):
                for p in range(d*PPD,d*PPD+PPD):
                    hs=-shints[student_id][p]+sum([shints[student_id][pid] for pid in [x for x in range(d*PPD,d*PPD+PPD) if x!=p]])
                    model.add(
                        hs
                        +sum([rparams[(e,r,p1)] for e in suitable_events for r in self.problem.event_rooms[e] for p1 in [x for x in range(d*PPD,d*PPD+PPD) if x!=p] if p1 in self.problem.events[e]['P']])
                        -sum([rparams[(e,r,p)] for e in suitable_events for r in self.problem.event_rooms[e] if p in self.problem.events[e]['P']])  
                        +single_day_events[(student_id,d)]>=0
                    )
                for i in range(3,5):
                    threshold=PPD-(i*2)
                    for p in range(d*PPD,d*PPD+PPD-i+1):
                        previous_period=p-1
                        next_period=p+i
                        if previous_period<d*PPD:
                            hs=-sum([shints[student_id][pid] for pid in range(p,next_period)])+shints[student_id][next_period]
                            model.add(
                                hs
                                -sum([rparams[(e,r,pid)] for e in suitable_events for r in self.problem.event_rooms[e] for pid in range(p,next_period) if pid in self.problem.events[e]['P']])
                                +sum([rparams[(e,r,next_period)] for e in suitable_events for r in self.problem.event_rooms[e] if next_period in self.problem.events[e]['P']])
                                +consecutive_events[(student_id,d,i)][0]>=-(i-1)
                            )
                        else:
                            hs=shints[student_id][previous_period]-sum([shints[student_id][pid] for pid in range(p,next_period)])+shints[student_id][next_period]
                            model.add(
                                hs
                                +sum([rparams[(e,r,previous_period)] for e in suitable_events for r in self.problem.event_rooms[e] if previous_period in self.problem.events[e]['P']])
                                -sum([rparams[(e,r,pid)] for e in suitable_events for r in self.problem.event_rooms[e] for pid in range(p,next_period) if pid in self.problem.events[e]['P']])
                                +sum([rparams[(e,r,next_period)] for e in suitable_events for r in self.problem.event_rooms[e] if next_period in self.problem.events[e]['P']])
                                +consecutive_events[(student_id,d,i)][0]>=-(i-1)
                            )
                        

                        if p<threshold:
                            for p2 in range(next_period+1,d*PPD+PPD-i+1):
                                previous_period=p2-1
                                next_period2=p2+i

                                if next_period2==d*PPD+PPD-1:
                                    hs=-sum([shints[student_id][pid] for pid in range(p2,next_period2)])+shints[student_id][next_period2]
                                    model.if_then(
                                        consecutive_events[(student_id,d,i)][0],
                                        hs
                                        -sum([rparams[(e,r,pid)] for e in suitable_events for r in self.problem.event_rooms[e] for pid in range(p2,next_period2) if pid in self.problem.events[e]['P']])
                                        +sum([rparams[(e,r,next_period2)] for e in suitable_events for r in self.problem.event_rooms[e] if next_period2 in self.problem.events[e]['P']])
                                        +consecutive_events[(student_id,d,i)][1]>=-(i-1)
                                    )
                                else:
                                    hs=shints[student_id][previous_period]-sum([shints[student_id][pid] for pid in range(p2,next_period2)])+shints[student_id][next_period2]
                                    model.if_then(
                                        consecutive_events[(student_id,d,i)][0],
                                        hs
                                        -sum([rparams[(e,r,pid)] for e in suitable_events for r in self.problem.event_rooms[e] for pid in range(p2,next_period2) if pid in self.problem.events[e]['P']])
                                        +sum([rparams[(e,r,next_period2)] for e in suitable_events for r in self.problem.event_rooms[e] if next_period2 in self.problem.events[e]['P']])
                                        +consecutive_events[(student_id,d,i)][1]>=-(i-1)
                                    )
                
                for i in range(5,PPD+1):
                    for p in range(d*PPD,d*PPD+PPD):
                        previous_period=p-1
                        next_period=p+i

                        # period score function contribution
                        previous_period_contribution=shints[student_id][previous_period]+sum([rparams[(e,r,previous_period)] for e in suitable_events for r in self.problem.event_rooms[e] if previous_period in self.problem.events[e]['P']]) if previous_period>=d*PPD else 0
                        i_consecutive_periods_contribution=-sum([rparams[(e,r,pid)] for e in suitable_events for r in self.problem.event_rooms[e] for pid in range(p,next_period)])-sum([shints[student_id][pid] for pid in range(p,next_period)])
                        next_period_contribution=shints[student_id][next_period]+sum([rparams[(e,r,next_period)] for e in suitable_events for r in self.problem.event_rooms[e] if next_period in self.problem.events[e]['P']]) if next_period<=d*PPD+PPD-1 else 0

                        model.add(
                            previous_period_contribution
                            +i_consecutive_periods_contribution
                            +next_period_contribution
                            +consecutive_events[(student_id,d,i)]>=-(i-1)
                        )
        
        objective=[
            sum([single_day_events[(student_id,d)] for student_id in event_students for d in range(D)])
            ,sum([consecutive_events[(student_id,d,i)][j]*(i-2) for student_id in event_students for d in range(D) for i in range(3,5) for j in [0,1]])
            ,sum([consecutive_events[(student_id,d,i)]*(i-2) for student_id in event_students for d in range(D) for i in range(5,PPD+1)])
            ,sum([rparams[(e,r,p)] for e in self.rooms[rid] for r in self.problem.event_rooms[e] for p in self.problem.last_period_per_day if p in self.problem.events[e]['P']])
        ]        
        
        model.minimize(
            sum(objective)
        )

        params=cpx.CpoParameters()
        params.LogPeriod=5000
        params.TimeLimit=100
        params.Workers=os.cpu_count()

        solver=model.solve(params=params)
        esol={}
        if solver:
            for (e,r,p) in rparams.items():
                esol[e]=(r,p)
        
        return esol

    def can_be_moved(self,move_type='period',elements={},exclude=[]):
        if move_type=='period':
            e=elements['event']
            p=elements['period']

            for e2 in self.problem.G.neighbors(e):
                if e2 in exclude: continue
                if self.psolution[e2]==p:
                    return False
            return True
        
        elif move_type=='room':
            e=elements['event']
            r=elements['room']

            for e2 in self.problem.G.neighbors(e):
                if e2 in exclude: continue
                if self.rsolution[e2]==r:
                    return False
            return True
        
        elif move_type=='both':
            e=elements['event']
            r=elements['room']
            p=elements['period']

            for e2 in self.problem.G.neighbors(e):
                if e2 in exclude: continue
                if self.rsolution[e2]==r:
                    return False
                if self.psolution[e2]==p:
                    return False
            return True


    def transfer(self):
        e=random.sample(self.problem.G.nodes)
        p=random.randint(0,P-1)
        while p==self.psolution[e]:
            p=random.randint(0,P-1)
        
        if self.can_be_moved(move_type='period',elements={'event':e,'period':p}):
            return {e:p}
        return dict()
    
    def swap(self):
        e=random.sample(self.problem.G.nodes)
        e2=random.sample(self.problem.G.nodes)
        while e==e2:
            e2=random.sample(self.problem.G.nodes)
        
        if self.can_be_moved(move_type='period',elements={'event':e,'period':self.psolution[e2]},exclude=[e2]) and self.can_be_moved(move_type='period',elements={'event':e2,'period':self.psolution[e]},exclude=[e]):
            return {
                e:self.psolution[e2],
                e2:self.psolution[e]
            }
        return dict()
    
    def kempe_chain(self):
        e=random.sample(self.problem.G.nodes)
        e2=random.sample(self.problem.G.nodes)
        while e==e2:
            e2=random.sample(self.problem)
        
        versus_period={
            self.psolution[e]:self.psolution[e2],
            self.psolution[e2]:self.psolution[e]
        }
        kc=LifoQueue()
        kc.put(e)
        moves={}

        while not kc.empty():
            current_event=kc.get()
            current_period=self.psolution[current_event]
            new_period=versus_period[current_period]
            if new_period not in self.problem.events[current_event]['P']:
                return dict()
            moves[current_event]=new_period

            for eid in self.problem.G.neighbors(current_event):
                if eid in moves: continue
                if self.psolution[eid]==new_period:
                    kc.put(eid)
        return moves

    def kempe_chain_room(self,moves):
        periods_used=set(moves.values())
        sol_hints=self.create_solution_hints()

        model=cpx.CpoModel()
        dparams={(e,r,p):model.binary_var(name=f'dvar_{e}_{r}_{p}') for e in moves.keys() for r in self.problem.event_rooms[e] for p in periods_used}

        for e in moves.keys():
            model.add(
                sum([dparams[(e,r,p)] for r in self.problem.event_rooms[e] for p in periods_used])==1
            )
        
        for r in self.problem.rooms.keys():
            for p in periods_used:
                model.add(
                    sum([dparams[(e,r,p)] for e in moves.keys() if r in self.problem.event_rooms[e]])
                    +sol_hints[r][p]<=1
                )
        
        ehints=self.create_event_hints(moves.keys())
        for e in moves.keys():
            for e2 in self.problem.G.neighbors(e):
                for p in periods_used:
                    if p not in self.problem.events[e]['P'] or p not in self.problem.events[e2]['P']: continue
                    if e2 in moves.keys():
                        model.add(
                            sum([dparams[(e,r,p)] for r in self.problem.event_rooms[e]])
                            +sum([dparams[(e2,r,p)] for r in self.problem.event_rooms[e2]])
                            <=1
                        )
                    else:
                        model.add(
                            sum([dparams[(e,r,p)] for r in self.problem.event_rooms[e]])
                            +ehints[e2][p]<=1
                        )
        
        shints=self.create_student_hints(moves.keys())
        days={p//PPD for p in moves.values()}
        participants={student_id for e in moves.keys() for student_id in self.problem.events[e]['S']}
        single_day_events={(student_id,d):model.binary_var(name=f'single_day_events_for_{student_id}_{d}') for student_id in participants for d in days}
        consecutive_events={(student_id,d,i):[model.binary_var(name=f'consecutive_events_for_{student_id}_{d}_{i}_0'),model.binary_var(name=f'consecutive_events_for_{student_id}_{d}_{i}_1')] for student_id in participants for d in days for i in range(3,5)}
        consecutive_events.update({(student_id,d,i):model.binary_var(namer=f'consecutive_events_for_{student_id}_{d}_{i}') for student_id in participants for d in days for i in range(5,PPD+1)})

        for student_id in participants:
            suitable_events=list(set(self.problem.students[student_id]).intersection(moves.keys()))
            for d in days:
                for p in range(d*PPD,d*PPD+PPD):
                    current_period_contribution=-sum([dparams[(e,r,p)] for e in moves.keys() for r in self.problem.event_rooms[e] if p in periods_used])-shints[student_id][p]
                    rest_periods_contribution=sum([dparams[(e,r,p1)] for e in suitable_events for r in self.problem.event_rooms[e] for p1 in [x for x in range(d*PPD,d*PPD+PPD) if x!=p] if p1 in periods_used])+sum([shints[student_id][pid] for pid in [x for x in range(d*PPD,d*PPD+PPD) if x!=p]])
                    model.add(
                        current_period_contribution
                        +rest_periods_contribution
                        +single_day_events[(student_id,d)]>=0
                    )

                for i in range(3,5):
                    pass

    def make_move(self):
        move_id=random.randint(1,3)
        if move_id==1:
            return self.transfer()
        elif move_id==2:
            return self.swap()
        elif move_id==3:
            return self.kempe_chain()