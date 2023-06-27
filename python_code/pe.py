import os
from collections import defaultdict
from enum import Enum
import networkx as nx
from itertools import combinations
from rich.console import Console
import matplotlib.pyplot as plt
import pandas as pd
from bokeh.io import show, output_file,output_notebook
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool
from bokeh.plotting import from_networkx
from bokeh.io.export import export_png
import networkx as nx
import screeninfo
from collections import defaultdict

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
    
    @staticmethod
    def to_sql():
        import sqlite3 as sql
        path_to_db=os.path.join('','instances','ditPECTThub.db')
        try:
            conn=sql.connect(path_to_db)
        except sql.Error as err:
            print(err)
        
        cursor=conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS PECTT(Id text,Formulation text,Events integer,Feature integer,Rooms integer,Students integer,Density real,Average_Room_Size real,Average_Room_suitability real,Cost integer)")


        for instance in Problem.get_instances():
            cursor.execute("INSERT INTO PECTT(Id,Formulation) VALUES(?,?)",instance.removesuffix('.tim'),PRF.get_formulation(instance))
        conn.commit()
        cursor.close()
        conn.close()

class Problem:
    path_to_datasets=os.path.join('.','instances')
    formulationDB=None
    
    @staticmethod
    def change_path_to_datasets(filepath):
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
        console.print(f'[bold green] Has precedence:{PRF.has_extra_constraints(self.formulation)}')

    def frozenrooms(self)->dict:
        distinct_rooms=dict()
        for event_id,room_events in self.event_available_rooms.items():
            froom_set=frozenset(room_events)
            if froom_set not in distinct_rooms:
                distinct_rooms[froom_set]=list()
            distinct_rooms[froom_set].append(event_id)    
        return distinct_rooms

    def create_hints(self,eset,solution_hint):
        hints={student_id:{period_id:False for period_id in range(self.P)} for student_id in range(self.S)}
        for event_id in range(self.E):
            if event_id in eset: continue
            for student_id in self.events[event_id]['S']:
                hints[student_id][solution_hint[event_id]['P']]=True
        return hints

    def create_event_hints(self,eset,solution_set):
        ehints={event_id:{(room_id,period_id):False for room_id in range(self.R) for period_id in range(self.P)} for event_id in range(self.E)}
        for event_id in range(self.E):
            if event_id in eset: continue
            ehints[event_id][(solution_set[event_id]['R'],solution_set[event_id]['P'])]=True
        return ehints

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




    



