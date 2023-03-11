import os
from collections import defaultdict
from enum import Enum
import networkx as nx
from itertools import combinations
from rich.console import Console

class PRF(Enum):
    TTCOMP2002=1,
    ITC2007=2,
    HarderLewisPaechter=3,
    MetaheuristicsNetwork=4

    @staticmethod
    def has_extra_constraints(problem_formulation):
        return problem_formulation==PRF.ITC2007 or problem_formulation==PRF.HarderLewisPaechter


class Problem:
    path_to_datasets=os.path.join('','instances')
    def __init__(self):
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
    
    def read(self,file_id):
        with open(os.path.join(Problem.path_to_datasets,file_id),'r') as RF:
            self.E,self.R,self.F,self.S=[int(x) for x in RF.readline().strip().split()]
            self.events={eid:{"S":set(),"F":set(),"HPE":list()} for eid in range(self.E)}
            self.rooms={rid:{"C":-1,"F":set()} for rid in range(self.R)}
            self.event_combinations=dict()

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
                        if int(RF.readline.strip())==1:
                            self.event_available_periods[eid].append(pid)
                
                # 6. Event-Event priority relations
                for eid in range(self.E):
                    for eid2 in range(self.E):
                        line=RF.readline()
                        if line=="":
                            break
                        elif int(line)==1:
                            self.events[eid]["HPE"].append(eid2)
                        elif int(line)==-1:
                            self.events[eid2]["HPE"].append(eid)
        
        # 7. Find available rooms per event and create the problem Graph using networkx
        for eid in range(self.E):
            for rid in range(self.R):
                if self.events[eid]['F'].is_subset(self.rooms[eid]['R']) and self.rooms[rid]['F']>=len(self.events[eid]['S']):
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
            for combination in combinations(events):
                self.event_combinations[frozenset(combination)]=self.event_combinations[frozenset(combination)]+1
    
    def statistics(self):
        self.conflict_density=nx.density(self.G)
        self.average_room_size=sum([self.rooms[rid]['C'] for rid in range(self.R)])/self.R
        self.average_event_period_unavailability=sum([self.P-len(self.event_available_periods[eid]) for eid in range(self.E)])/(self.E*self.P)
        self.average_room_suitability=sum([len(self.event_available_rooms[eid]) for eid in range(self.E)])/(self.R*self.E)

        console=Console()
        console.rule('[bold red] Statistics')
        console.print(f'Events:{self.E}')
        console.print(f'Features:{self.F}')
        console.print(f'Rooms:{self.R}')
        console.print(f'Students:{self.S}')
        console.print(f'Conflict Density:{self.conflict_density}')
        console.print(f'Average room size:{self.average_room_size}')
        console.print(f'Average room suitability:{self.average_room_suitability}')
        console.print(f'Average event period unavailability:{self.average_event_period_unavailability}')

    def room_availability(self):
        # Visualize room availability in heatmap
        pass

if __name__=='__main__':
    pass
