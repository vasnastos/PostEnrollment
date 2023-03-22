import os
from collections import defaultdict
from enum import Enum
import networkx as nx
from itertools import combinations
from rich.console import Console
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sn

from bokeh.io import show, output_file,output_notebook
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool
from bokeh.plotting import from_networkx
from bokeh.io.export import export_png
import networkx as nx
import screeninfo

from collections import defaultdict,Counter
import random,time
from queue import LifoQueue


class PRF(Enum):
    TTCOMP2002=1,
    ITC2007=2,
    HarderLewisPaechter=3,
    MetaheuristicsNetwork=4

    @staticmethod
    def has_extra_constraints(problem_formulation):
        return problem_formulation==PRF.ITC2007
    
    @staticmethod
    def get_formulation(filename):
        if type(Problem.formulationDB)!=pd.DataFrame:
            Problem.formulationDB=pd.read_excel(os.path.join(Problem.path_to_datasets,'descriptive_ds.xlsx'),header=0)
            print(Problem.formulationDB)
        
        check_vals=Problem.formulationDB['instance'].str.contains(filename)
        true_indeces=check_vals.index[check_vals==True].to_list()
        if len(true_indeces)==0:
            raise ValueError(f"Filename {filename} is not a valid filename")
        elif len(true_indeces)>1:
            raise ValueError(f'Filename {filename} is a duplicated record in the system')
        named_category=Problem.formulationDB.iloc[true_indeces[0]]['category']
        return PRF.TTCOMP2002 if named_category=="TTCOMP-2002" else PRF.ITC2007 if named_category=="ITC-2007" else PRF.HarderLewisPaechter if named_category=="Harder-(Lewis and Paechter)" else PRF.MetaheuristicsNetwork

    @staticmethod
    def named_formulation(formulation):
        return "original" if formulation==PRF.HarderLewisPaechter or formulation==PRF.MetaheuristicsNetwork else "full"

class Problem:
    path_to_datasets=os.path.join('.','instances')
    formulationDB=None
    
    @staticmethod
    def change_path_to_datasets(self,filepath):
        Problem.path_to_datasets=filepath

    @staticmethod
    def get_instances(formulations='all'):
        if isinstance(formulations,str):
            if formulations=='all':
                return [x for x in os.listdir(Problem.path_to_datasets) if x.endswith('.tim')]
            else:
                raise ValueError("No such dataset type")
        else:
            for formulation in formulations:
                if type(formulation)!=PRF:
                    raise ValueError("Unknown type of formulations")
            return [x for x in [x for x in os.listdir(Problem.path_to_datasets) if x.endswith('.tim') and x!='toy.tim'] if PRF.get_formulation(x) in formulations]


    def __init__(self):
        self.id=None
        self.events=defaultdict(dict)
        self.rooms=defaultdict(dict)
        self.students=defaultdict(list)
        self.event_available_periods=defaultdict(list)
        self.event_available_rooms=defaultdict(list)
        self.formulation=None
        self.days=5
        self.periods_per_day=9
        self.P=self.days * self.periods_per_day

        self.last_period_per_day=[day*self.periods_per_day+self.periods_per_day-1 for day in range(self.days)]

        self.E=-1
        self.R=-1
        self.F=-1
        self.S=-1

        self.conflict_density=-1
        self.average_room_suitability=-1
        self.average_room_size=-1
        self.average_event_period_unavailability=-1
        self.total_clash=0
    
    def clashe(self,event_id):
        if event_id not in self.events.keys():
            raise ValueError("No such event appears in the Graph")

        return len(self.G.neighbors(event_id))

    def read(self,file_id):
        self.id=file_id.removesuffix(".tim")
        self.formulation=PRF.get_formulation(file_id)
        with open(os.path.join(Problem.path_to_datasets,file_id),'r') as RF:
            self.E,self.R,self.F,self.S=[int(x) for x in RF.readline().strip().split()]
            self.events={eid:{"S":set(),"F":set(),"HPE":list()} for eid in range(self.E)}
            self.rooms={rid:{"C":-1,"F":set()} for rid in range(self.R)}
            self.event_combinations=dict()
            self.event_available_periods={event_id:[period_id for period_id in range(self.P)] for event_id in range(self.E)}

            # Room-capacity relations
            for rid in range(self.R):
                self.rooms[rid]['C']=int(RF.readline().strip())

            # 2. Event-Student relations
            for eid in range(self.E):
                for sid in range(self.S):
                    if int(RF.readline().strip())==1:
                        self.events[eid]['S'].add(sid)
                        self.students[sid].append(eid)
            
            # 3. Room-Feature relations
            for rid in range(self.R):
                for fid in range(self.F):
                    if int(RF.readline())==1:
                        self.rooms[rid]['F'].add(fid)
            
            # 4. Event-Feature relations
            for eid in range(self.E):
                for fid in range(self.F):
                    if int(RF.readline().strip()==1):
                        self.events[eid]['F'].add(fid)
            
            if PRF.has_extra_constraints(self.formulation):
                # 5. Event-Period availability
                for eid in range(self.E):
                    for pid in range(self.P):
                        if int(RF.readline().strip())==0:
                            self.event_available_periods[eid].remove(pid)
                
                # 6. Event-Event priority relations
                for eid in range(self.E):
                    for eid2 in range(self.E):
                        line=RF.readline().strip()
                        if line=="":
                            break
                        elif int(line)==1:
                            self.events[eid]["HPE"].append(eid2)
                        elif int(line)==-1:
                            self.events[eid2]["HPE"].append(eid)
        
        # 7. Find available rooms per event and create the problem Graph using networkx
        for eid in range(self.E):
            for rid in range(self.R):
                if self.events[eid]['F'].issubset(self.rooms[rid]['F']) and self.rooms[rid]['C']>=len(self.events[eid]['S']):
                    self.event_available_rooms[eid].append(rid)
        

        self.G=nx.Graph()
        self.G.add_nodes_from(list(self.events.keys()))
        for eid in range(self.E):
            for eidn in range(eid+1,self.E):
                common_students=len(self.events[eid]['S'].intersection(self.events[eidn]['S']))
                if common_students>0:
                    self.G.add_edge(eid,eidn,weight=common_students)
                
                elif self.event_available_rooms[eid]==self.event_available_rooms[eidn] and len(self.event_available_rooms[eid])==1:
                    self.G.add_edge(eid,eidn,weight=1)
        
        for events in self.students.values():
            for combination in combinations(events,3):
                self.event_combinations[frozenset(combination)]=self.event_combinations.get(frozenset(combination),0)+1

        self.total_clash=self.G.number_of_edges()
    
    def create_hints(self,eset,solution_hint):
        student_set={student_id for event_id in eset for student_id in self.events[event_id]['S']}
        hints={student_id:{period_id:False for period_id in range(problem.P)} for student_id in student_set}
        for event_id in eset:
            for student_id in problem.events[event_id]['S']:
                hints[student_id][solution_hint[event_id]['P']]=True
        return hints

    def statistics(self):
        self.conflict_density=nx.density(self.G)
        self.average_room_size=sum([self.rooms[rid]['C'] for rid in range(self.R)])/self.R
        self.average_event_period_unavailability=sum([self.P-len(self.event_available_periods[eid]) for eid in range(self.E)])/(self.E*self.P)
        self.average_room_suitability=sum([len(self.event_available_rooms[eid]) for eid in range(self.E)])/(self.R*self.E)

        console=Console()
        console.rule('[bold red] Insights')
        console.print(f'[bold blue]Dataset:{self.id}')
        console.print(f'[bold green]Events:{self.E}')
        console.print(f'[bold green]Features:{self.F}')
        console.print(f'[bold green]Rooms:{self.R}')
        console.print(f'[bold green]Students:{self.S}')
        console.print(f'[bold green]Periods:{self.P}')
        console.print(f'[bold green]Formulation:{PRF.named_formulation(self.formulation)}')
        console.print(f'[bold green]Conflict Density:{self.conflict_density}')
        console.print(f'[bold green]Average room size:{self.average_room_size}')
        console.print(f'[bold green]Average room suitability:{self.average_room_suitability}')
        console.print(f'[bold green]Average event period unavailability:{self.average_event_period_unavailability}',end='\n\n')
        console.print(f'[bold green] Has precedence')

    def student_enrollment(self):
        """
             A bar chart or pie chart can be created to show the number of students enrolled 
             in each course. This can help identify courses that are over- or under-subscribed, 
             and inform decisions about course scheduling and resource allocation.
        """
        
        enrollments=[len(self.events[eid]['S']) for eid in range(self.E)]
        mean_enrollments=sum(enrollments)/self.S

        sm = plt.cm.ScalarMappable(cmap='viridis')
        sm.set_array([])  # set empty array to initialize
        plt.figure(figsize=(15,12))
        plt.xticks(np.arange(0,self.E,25))
        plt.bar(np.arange(self.E),enrollments,color=sm.to_rgba(enrollments),width=5)
        plt.axhline(y=mean_enrollments,color='red',linewidth=3)
        ax=plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.show()
    
    def plot_graph(self):
        screen = screeninfo.get_monitors()[1]
        output_notebook()
        plot = Plot(title="Large Graph Visualization with Bokeh", x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1),width=screen.width, height=screen.height)

        graph_renderer = from_networkx(self.G, nx.spring_layout, scale=1, center=(0, 0))

        graph_renderer.node_renderer.glyph = Circle(size=10, fill_color='red')
        graph_renderer.edge_renderer.glyph = MultiLine(line_color='gray', line_alpha=0.4, line_width=0.5)
        plot.renderers.append(graph_renderer)

        hover = HoverTool(tooltips=[('index', f'Event_@index')])
        plot.add_tools(hover)

        output_file(f"{self.id}.html")
        show(plot)
        export_png(plot,filename=os.path.join('','figures',f'{self.id}.png'))


class Solution:
    def __init__(self,ds_name):
        self.problem=Problem()
        self.problem.read(ds_name)
        self.solution_set={event_id:{"P":-1,"R":-1} for event_id in range(self.problem.E)}
        self.roomwise_solutions=defaultdict(list)
        self.periodwise_solutions=defaultdict(list)
        self.room_period_availability=defaultdict(dict)
        self.cost=0
        random.seed(time.time())
        self.memory=dict()
    
    def compute_cost(self):
        ecost=0
        # Cost computation calculation
        for student_id in range(self.problem.S):
            consecutive=0
            student_participate_in=set([self.solution_set[event_id]["P"] for event_id in self.problem.students[student_id]])
            for day in range(self.problem.days):
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
        
        for event_id in range(self.problem.E):
            if self.solution_set[event_id]['P'] in self.problem.last_period_per_day:
                ecost+=len(self.problem.events[event_id]['S'])

        return ecost

    def compute_partial_cost(self,current_solution):
        ecost=0

        for student_id in range(self.problem.S):
            student_periods=[current_solution[event_id] for event_id in self.problem.students[student_id] if event_id in current_solution]
            for day in range(self.problem.days):
                consecutive=0
                for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day):
                    if period_id in student_periods:
                        consecutive+=1
                    else:
                        if consecutive>2:
                            ecost+=(consecutive-2)
                        consecutive=0
        return ecost        

    def compute_daily_cost(self,day):
        day_events=[event_id for event_id,sol_params in self.solution_set.items() if sol_params['P']//self.problem.periods_per_day==day]
        students_in_events=list(set([student_id for event_id in day_events for student_id in self.problem.events[event_id]['S']]))

        dcost=0
        for student_id in students_in_events:
            consecutive=0
            periods_in_day=[self.solution_set[event_id]['P'] for event_id in self.problem.students[student_id] if event_id in day_events]
            for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day):
                if period_id in periods_in_day:
                    consecutive+=1
                else:
                    if consecutive>2:
                        dcost+=(consecutive-2)
                    consecutive=0
            if consecutive>2:
                dcost+=(consecutive-2)
            dcost+=(len(periods_in_day)==1)
        dcost+=sum([len(self.problem.events[event_id]['S']) for event_id in day_events if self.solution_set[event_id]['P']==day*self.problem.periods_per_day+self.problem.periods_per_day-1])
        return dcost

    def can_be_moved(self,event_id,period_id,excluded=[]):
        if period_id not in self.problem.event_available_periods[event_id]:
            return False
        for neighbor_id in list(self.problem.G.neighbors(event_id)):
            if neighbor_id in excluded: continue
            if period_id==self.solution_set[neighbor_id]['P']:
                return False
        if PRF.has_extra_constraints(self.problem.formulation):
            for event_id2 in self.problem.events[event_id]['HPE']:
                if period_id>=self.solution_set[event_id2]['P']:
                    return False
        return True

    def room_available(self,period_id,room_id,excluded=[]):
        for event_id2 in self.roomwise_solutions[room_id]:
            if event_id2 in excluded:
                continue
            if period_id==self.solution_set[event_id2]['P']:
                return False
        return True

    def schedule(self,event_id,room_id,period_id):
        partial_cost=0
        event_students=self.problem.events[event_id]['S']
        day=period_id//self.problem.periods_per_day

        for student_id in event_students:
    
            student_periods=[self.solution_set[event_id2]['P'] for event_id2 in self.problem.students[student_id]]
            events_in_days=Counter([period_id//self.problem.periods_per_day for period_id in student_periods])

            if events_in_days.get(day,0)==0:
                partial_cost+=1
                continue
            
            elif events_in_days.get(day,0)==1 and student_periods[0]!=period_id:
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
        day=self.solution_set[event_id]['P']//self.problem.periods_per_day
        
        for student_id in event_students:
            student_periods=[self.solution_set[event_id2]['P'] for event_id2 in self.problem.students[student_id]]
            events_in_day=Counter([period_id//self.problem.periods_per_day for period_id in student_periods])
            if events_in_day.get(day,0)==1:
                partial_cost-=1
            elif events_in_day.get(day,0)==2:
                partial_cost+=1
            else:
                # A. Find consecutive events before period deletion 
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
                if self.solution_set[event_id]['P']!=-1:
                    student_periods.remove(self.solution_set[event_id]['P'])
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

        if self.solution_set[event_id]['P']!=-1:
            self.periodwise_solutions[self.solution_set[event_id]['P']].remove(event_id)
            self.roomwise_solutions[self.solution_set[event_id]['R']].remove(event_id)
        self.solution_set[event_id]['P']=-1
        self.solution_set[event_id]['R']=-1    
        return partial_cost

    def transfer_event(self):
        event_id=random.randint(0,self.problem.E-1)
        candicate_period=random.randint(0,self.problem.P)
    
        if self.can_be_moved(event_id,candicate_period):
            for room_id in self.problem.event_available_rooms[event_id]:
                if self.room_available(room_id,candicate_period):
                    return {event_id:(candicate_period,room_id)}

        return dict()
    
    def swap_events(self):
        potential_move=dict()
        event_id=random.randint(0,self.problem.E-1)
        event_id2=random.randint(0,self.problem.E-1)
        while event_id==event_id2:
            event_id2=random.randint(0,self.problem.E-1)


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
                    if room_id in [self.solution_set[event_id]['R'],self.solution_set[event_id2]['R']]:
                        continue
                    if self.room_available(self.solution_set[event_id2]['P'],room_id):
                        potential_move[event_id]=(self.solution_set[event_id2]['P'],room_id)
                
                if event_id not in potential_move: 
                    return dict()

                for room_id in self.problem.event_available_rooms[event_id2]:
                    if room_id in [self.solution_set[event_id]['R'],self.solution_set[event_id2]['R']]:
                        continue
                    if self.room_available(self.solution_set[event_id]['P'],room_id):
                        potential_move[event_id]=(self.solution_set[event_id2]['P'],room_id)

                if event_id2 not in potential_move: 
                    return dict()
                    
        return potential_move

    def kempe_chain(self):
        kc=LifoQueue()
        event_id1=random.randint(0,self.problem.E-1)
        event_id2=None
        eneighbors=list(self.problem.G.neighbors(event_id1))
        valid_move=False
        while len(eneighbors)==0 and not valid_move:
            event_id1=random.randint(0,self.problem.E-1)
            eneighbors=self.problem.G.neighbors(event_id1)
            for event_id_neighbor in eneighbors:
                valid_move=(self.solution_set[event_id_neighbor]['P'] in self.problem.event_available_periods[event_id] and self.solution_set[event_id]['P'] in self.problem.event_available_periods[event_id_neighbor])
                if valid_move:
                    event_id2=event_id_neighbor
                    break 
        if event_id2==None: return dict()
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
            eneighbors=self.problem.G.neighbors(current_event)
            for neighbor in eneighbors:
                if neighbor in moves: continue
                if self.solution_set[neighbor]['P']==new_period:
                    kc.put(neighbor)
        
        potential_solution={}
        for event_id,period_id in moves.items():
            found=False
            for room_id in self.problem.event_available_rooms[event_id]:
                if self.room_available(period_id,room_id,excluded=[event_id]):
                    potential_solution[event_id]=(period_id,room_id)
            if not found:
                return dict()
        return potential_solution

    def kick(self):
        pass

    def select_operator(self):
        operator_choice=random.randint(1,2)
        # operator_choice=1
        if operator_choice==1:
            return self.transfer_event(),"TRANSFER"
        elif operator_choice==2:
            return self.swap_events(),"SWAP"
        elif operator_choice==3:
            return self.kempe_chain(),"KEMPE CHAIN"
        else:
            raise ValueError(f"Operator {operator_choice} does not implement yet")

    def reposition(self,moves):
        for event_id,(period_id,room_id) in moves.items():
            self.memory[event_id]=(period_id,room_id)
            self.cost+=self.unschedule(event_id)
            self.cost+=self.schedule(event_id,room_id,period_id)

    def rollback(self):
        for event_id,(period_id,room_id) in self.memory.items():
            self.cost+=self.unschedule(event_id)
            self.cost+=self.schedule(event_id,room_id,period_id)
        self.memory.clear()

    def validator(self):
        infeasibilities=0
        penalty=0
        last_timeslot_penalty=0
        console=Console(record=True)
        console.rule('[bold red]Infeasibilities')
        for student_id in range(self.problem.S):
            students_penalty=0
            single_event_day=0
            for day in range(self.problem.days):
                consecutive=0
                periods_in_day=[self.solution_set[event_id]['P'] for event_id in self.problem.students[student_id] if self.solution_set[event_id]['P']//self.problem.periods_per_day==day]
                if len(periods_in_day)==1:
                    single_event_day+=1
                elif len(periods_in_day)>2:
                    for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day):
                        if period_id in periods_in_day:
                            consecutive+=1  
                        else:
                            if consecutive>2:
                                students_penalty+=(consecutive-2)
                            consecutive=0

                    if consecutive>2:
                        students_penalty+=(consecutive-2)
                    consecutive=0

            console.print(f'[bold red]Student_id:{student_id}\tSingle Event days {single_event_day}/{self.problem.days}')
            console.print(f'[bold red]Student_id:{student_id}\tConsecutive Events Penalty:{students_penalty}')
            penalty+=single_event_day+students_penalty

        console.log('[bold blue]Period Infeasibilities')
        for event_id in range(self.problem.E):
            if self.solution_set[event_id]['P'] in self.problem.last_period_per_day:
                last_timeslot_penalty+=len(self.problem.events[event_id]['S'])

            for neighbor_id in list(self.problem.G.neighbors(event_id)):
                if self.solution_set[event_id]['P']==self.solution_set[neighbor_id]['P']:
                    console.print(f'[bold red]Infeasibility tracked: E{event_id}->E{neighbor_id}')
                    infeasibilities+=1
        
        penalty+=last_timeslot_penalty

        console.log('[bold red]Room infeasibilities')
        for period_id in range(self.problem.P):
            room_placement=Counter(self.periodwise_solutions[period_id])
            for room_id,no_events in room_placement.items():
                if no_events>1:
                    console.log(f'Room {room_id}: Total placements:{no_events}')
        
        console.print(f'Last timeslot penalty:{last_timeslot_penalty}')
        console.print(f'Total penalty:{penalty}')
        console.print(f'Total number of infeasibilities tracked:{infeasibilities}')
        
    def set_solution(self,candicate_solution):
        is_init=(len([event_id for event_id in range(self.problem.E) if self.solution_set[event_id]['P']==-1 and self.solution_set[event_id]['R']==-1])==self.problem.E)
        for event_id,(period_id,room_id) in candicate_solution.items():
            if not is_init:
                self.cost+=self.unschedule(event_id)
            self.cost+=self.schedule(event_id,room_id,period_id)
            print(self.cost)
    
    def save(self,filepath):
        self.solution_set=dict(sorted(self.solution_set.items(),key=lambda e:e[0]))
        with open(filepath,'w') as writer:
            for _,sol_set in self.solution_set.items():
                writer.write(f'{sol_set["P"]} {sol_set["R"]}\n')

if __name__=='__main__':
    problem=Problem()
    problem.read('i20.tim')
    problem.statistics()
    problem.plot_graph()
