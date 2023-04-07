from collections import defaultdict,Counter
from pe import Problem,PRF
from rich.console import Console
import random,time,os
from queue import LifoQueue
from itertools import combinations

# Solvers
import docplex.cp.model as cpx
from ortools.sat.python import cp_model
import gurobipy as gp

class Solution:
    path_to_simulated_annealing_results=os.path.join('','results','simulated_annealing')

    @staticmethod
    def load_initial_solution(problem_id:str):
        for fn in os.listdir(Solution.path_to_simulated_annealing_results):
            if fn.startswith(problem_id):
                with open(os.path.join(Solution.path_to_simulated_annealing_results,fn)) as reader:
                    solution=dict()
                    for event_id,line in enumerate(reader):
                        period_id,room_id=[int(x) for x in line.split()]
                        solution[event_id]=(period_id,room_id)
                    return solution
        return None

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
                if event_id2 in excluded: continue
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
            else:
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
        
        self.cost+=partial_cost
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
        candicate_period=random.randint(0,self.problem.P-1)
    
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
        eneighbors=self.problem.G.neighbors(event_id1)
        event_id2=None
        for event_id2 in eneighbors:
            valid_move=self.can_be_moved(event_id1,self.solution_set[event_id2]['P'],excluded=[event_id2]) and self.can_be_moved(event_id2,self.solution_set[event_id1]['P'],excluded=[event_id1])
            if not valid_move:
                continue
                
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
                eneighbors=self.problem.G.neighbors(current_event)
                if self.can_be_moved(current_event,new_period,excluded=list(moves.keys())):
                    moves[current_event]=new_period
                    for neighbor in eneighbors:
                        if neighbor in moves: continue
                        if self.solution_set[neighbor]['P']==new_period:
                            kc.put(neighbor)
                else:
                    return dict()
                
            potential_solution={}
            for event_id,period_id in moves.items():
                found=False
                for room_id in self.problem.event_available_rooms[event_id]:
                    if self.room_available(period_id,room_id,excluded=[event_id]):
                        potential_solution[event_id]=(period_id,room_id)
                        found=True
                if not found:
                    return dict()
            return potential_solution

    def kick(self):
        event_id1=random.randint(0,self.problem.E-1)
        for event_id2 in self.problem.G.neighbors(event_id1):    
            potential_solution=dict()
            if self.can_be_moved(event_id1,self.solution_set[event_id2]['P'],excluded=[event_id2]):
                for room_id in range(self.problem.R):
                    if self.room_available(self.solution_set[event_id2]['P'],room_id):
                        potential_solution[event_id1]=(self.solution_set[event_id2]['P'],room_id)
            
            if event_id1 in potential_solution:
                previous_day=self.solution_set[event_id2]['P']//self.problem.periods_per_day
                for new_event2_period in [pid for pid in range(self.problem.P) if pid//self.problem.periods_per_day!=previous_day]:
                    if self.can_be_moved(event_id2,new_event2_period,excluded=[event_id1]):
                        for room_id in range(self.problem.R):
                            if self.room_available(event_id2,new_event2_period):
                                potential_solution[event_id2]=(new_event2_period,room_id)
                                break
                        if event_id2 in potential_solution:
                            return potential_solution
        return dict()


    def select_operator(self):
        operator_choice=random.randint(1,5)
        if operator_choice==1:
            return self.transfer_event(),"TRANSFER"
        elif operator_choice==2:
            return self.swap_events(),"SWAP"
        elif operator_choice==3:
            return self.kempe_chain(),"KEMPE CHAIN"
        elif operator_choice==4:
            return self.kick(),"KICK"
        elif operator_choice==5:
            daily_cost=sorted({day:self.compute_daily_cost(day) for day in range(self.problem.days)}.items(),key=lambda x:x[1],reverse=True)
            moves=dict()
            days=[daily_cost[i][0] for i in range(2)]
            for day in days:
                moves.update(self.day_by_day(day))
            return moves,"DAY BY DAY"
            
        else:
            raise ValueError(f"Operator {operator_choice} does not implement yet")

    def reposition(self,moves):
        for event_id,(period_id,room_id) in moves.items():
            self.memory[event_id]=(self.solution_set[event_id]['P'],self.solution_set[event_id]['R'])
            self.cost+=self.unschedule(event_id)
            self.cost+=self.schedule(event_id,room_id,period_id)

    def rollback(self):
        for event_id,(period_id,room_id) in self.memory.items():
            self.cost+=self.unschedule(event_id)
            self.cost+=self.schedule(event_id=event_id,room_id=room_id,period_id=period_id)
        self.memory.clear()

    def is_feasible(self,verbose=False):
        infeasibilities=0
        penalty=0
        last_timeslot_penalty=0
        console=Console(record=True)
        if verbose:
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
            if verbose:
                console.print(f'[bold red]Student_id:{student_id}\tSingle Event days {single_event_day}/{self.problem.days}')
                console.print(f'[bold red]Student_id:{student_id}\tConsecutive Events Penalty:{students_penalty}')
            penalty+=single_event_day+students_penalty

        if verbose:
            console.log('[bold blue]Period Infeasibilities')
        for event_id in range(self.problem.E):
            if self.solution_set[event_id]['P'] in self.problem.last_period_per_day:
                last_timeslot_penalty+=len(self.problem.events[event_id]['S'])

            for neighbor_id in list(self.problem.G.neighbors(event_id)):
                if self.solution_set[event_id]['P']==self.solution_set[neighbor_id]['P']:
                    if verbose:
                        console.print(f'[bold red]Infeasibility tracked: E{event_id}->E{neighbor_id}')
                    infeasibilities+=1

            for event_id2 in self.problem.events[event_id]['HPE']:
                if self.solution_set[event_id]['P']>=self.solution_set[event_id2]['P']:
                    infeasibilities+=1
        
        penalty+=last_timeslot_penalty

        console.log('[bold red]Room infeasibilities')
        for period_id in range(self.problem.P):
            room_placement=Counter(self.periodwise_solutions[period_id])
            for room_id,no_events in room_placement.items():
                if no_events>1:
                    infeasibilities+=1
                    if verbose:
                        console.log(f'Room {room_id}: Total placements:{no_events}')
        if verbose:
            console.print(f'Last timeslot penalty:{last_timeslot_penalty}')
            console.print(f'Total penalty:{penalty}')
            console.print(f'Total number of infeasibilities tracked:{infeasibilities}')
        return infeasibilities==0

    def set_solution(self,candicate_solution):
        is_init=(len([event_id for event_id in range(self.problem.E) if self.solution_set[event_id]['P']==-1 and self.solution_set[event_id]['R']==-1])==self.problem.E)
        for event_id,(period_id,room_id) in candicate_solution.items():
            if not is_init:
                self.cost+=self.unschedule(event_id)
            self.cost+=self.schedule(event_id,room_id,period_id)
    
    def save(self,filepath):
        self.solution_set=dict(sorted(self.solution_set.items(),key=lambda e:e[0]))
        with open(filepath,'w') as writer:
            for _,sol_set in self.solution_set.items():
                writer.write(f'{sol_set["P"]} {sol_set["R"]}\n')
    
    # Exact solvers
    def create_timetable(self,tsolver='cp-sat',timesol=600):
        """
            Initial solution creator. It constructs 3 different solutions using 3 different models(cp-sat,cplex-Cp and gurobi-mip)
            Parameters:
                - self.problem: A self.problem instance load by class self.problem
                - csolver: The type of the solver is used for consructing initial solutions("cp-sat","cp-cplex","gurobi")
                - save: Format that the solution could be potential saved("txt","pickle","None")
                - timesol: time in seconds the the solver would run for
            Returns:
                - dict: contains the generated timetable
        """

        solution_dict=Solution.load_initial_solution(self.problem.id)
        if solution_dict:
            self.set_solution(solution_dict)
            return


        generated_solution={}
        if tsolver=='cp-sat':
            model=cp_model.CpModel()
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in range(self.problem.E) for room_id in range(self.problem.R) for period_id in range(self.problem.P)}

            # 1. One event should be placed in only one room in only one period
            for event_id in range(self.problem.E):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(self.problem.R)
                        for period_id in range(self.problem.P)
                    ])==1
                )
            
            # 2. Events should not be placed in non valid rooms or periods
            for event_id in range(self.problem.E):
                for room_id in range(self.problem.R):
                    if room_id not in self.problem.event_available_rooms[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                                for period_id in range(self.problem.P)
                            ])==0
                        )
                
                for period_id in range(self.problem.P):
                    if period_id not in self.problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])==0
                        )

            # 3. One event should be schedule at each period-room pair
            for room_id in range(self.problem.R):
                for period_id in range(self.problem.P):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in range(self.problem.E)
                        ])<=1
                    )


            # 4. Add neighborhood constraints
            for event_id in range(self.problem.E):
                for neighbor_id in list(self.problem.G.neighbors(event_id)):
                    for period_id in range(self.problem.P):
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])+sum([
                                xvars[(neighbor_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])<=1
                        )

            # 5. Add precedence relations
            if PRF.has_extra_constraints(self.problem.formulation):
                for event_id in range(self.problem.E):
                    for event_id2 in self.problem.events[event_id]['HPE']:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)] * period_id
                                for room_id in range(self.problem.R)
                                for period_id in range(self.problem.P)
                            ])<sum([
                                xvars[(event_id2,room_id,period_id)] * period_id
                                for room_id in range(self.problem.R)
                                for period_id in range(self.problem.P)
                            ])
                        )

            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=timesol
            solver.parameters.num_search_workers=os.cpu_count()
            solver.parameters.log_search_progress=True
            status=solver.Solve(model,solution_callback=cp_model.ObjectiveSolutionPrinter)
            if status in [cp_model.FEASIBLE,cp_model.OPTIMAL]:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1:
                        generated_solution[event_id]=(period_id,room_id)
        
        elif  tsolver=="cp-cplex":
            model=cpx.CpoModel(name='post_enrollment_timetable_constructor')
            xvars={(event_id,room_id,period_id):model.binary_var(name={f"sd_{event_id}_{room_id}_{period_id}"}) for event_id in range(self.problem.E) for room_id in range(self.problem.R) for period_id in range(self.problem.P)}

            for event_id in range(self.problem.E):
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(self.problem.R)
                        for period_id in range(self.problem.P)
                    ])==1
                )
            
            # 2. Events should not be placed in non valid rooms or periods
            for event_id in range(self.problem.E):
                for room_id in range(self.problem.R):
                    if room_id not in self.problem.event_available_rooms[event_id]:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                                for period_id in range(self.problem.P)
                            ])==0
                        )
                
                for period_id in range(self.problem.P):
                    if period_id not in self.problem.event_available_periods[event_id]:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])==0
                        )

            # 3. One event should be schedule at each period-room pair
            for room_id in range(self.problem.R):
                for period_id in range(self.problem.P):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in range(self.problem.E)
                        ])<=1
                    )


            # 4. Add neighborhood constraints
            for event_id in range(self.problem.E):
                for neighbor_id in self.problem.G.neighbors(event_id):
                    for period_id in range(self.problem.P):
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])+sum([
                                xvars[(neighbor_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])<=1
                        )

            
            # 5. Add precedence relations
            if PRF.has_extra_constraints(self.problem.formulation):
                for event_id in range(self.problem.E):
                    for event_id2 in self.problem.events[event_id]['HPE']:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)] * period_id
                                for room_id in range(self.problem.R)
                                for period_id in range(self.problem.P)
                            ])<sum([
                                xvars[(event_id2,room_id,period_id)] * period_id
                                for room_id in range(self.problem.R)
                                for period_id in range(self.problem.P)
                            ])
                        )
            params=cpx.CpoParameters()
            params.TimeLimit=timesol
            params.Workers=os.cpu_count()
            solver=model.solve(params=params)

            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1:
                        generated_solution[event_id]=(room_id,period_id)

        elif tsolver=='gurobi':
            # Gurobi solver
            model=gp.Model(name="Gurobi_post_enrollment")
            xvars=model.addVars([(event_id,room_id,period_id) for event_id in range(self.problem.E) for room_id in range(self.problem.R) for period_id in range(self.problem.P)],vtype=gp.GRB.BINARY,name='xvars')

            for event_id in range(self.problem.E):
                model.addConstr(
                    xvars.sum(event_id,'*','*')==1,name=f'Constr_{event_id}'
                )
            
            for event_id in range(self.problem.E):
                for room_id in range(self.problem.R):
                    if room_id not in self.problem.event_available_rooms[event_id]:
                        model.addConstr(
                            xvars.sum(event_id,room_id,'*')==0
                        )
            
                for period_id in range(self.problem.P):
                    if period_id not in self.problem.event_available_periods[event_id]:
                        model.addConstr(
                            xvars.sum(event_id,'*',period_id)==0,name=f'Period_Constr_{event_id}'
                        )
            
            for room_id in range(self.problem.R):
                for period_id in range(self.problem.P):
                    model.addConstr(
                        xvars.sum('*',room_id,period_id)<=1,name=f'room_period_Constr_({room_id},{period_id})'
                    )
            
            for event_id in range(self.problem.E):
                for event_id2 in self.problem.G.neighbors(event_id):
                    for period_id in range(self.problem.P):
                        model.addConstr(
                            xvars.sum(event_id,'*',period_id)
                            +xvars.sum(event_id2,'*',period_id)<=1
                        )
            if PRF.has_extra_constraints(self.problem.formulation):
                for event_id in range(self.problem.E):
                    for event_id2 in self.problem.events[event_id]['HPE']:
                        model.addConstr(
                            sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(self.problem.R) for period_id in range(self.problem.P)])<
                            sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(self.problem.R) for period_id in range(self.problem.P)])
                        )
            
            model.Params.TimeLimit=timesol
            model.Params.Threads=os.cpu_count()
            model.optimize()

            if model.Status in [gp.GRB.OPTIMAL,not gp.GRB.INFEASIBLE]:
                for (event_id,room_id,period_id),decision_var in xvars.items():
                    if decision_var.X==1:
                        generated_solution[event_id]=(period_id,room_id)

        self.set_solution(generated_solution)

    def day_by_day(self,day):
        eset=[event_id for event_id,sol_vars in self.solution_set.items() if sol_vars['P']%self.problem.periods_per_day==day]
        event_combinations={frozenset(ecomb):self.problem.event_combinations[frozenset(ecomb)] for ecomb in combinations(eset,3) if frozenset(ecomb) in self.problem.event_combinations}

        generated_solution={}
        model=cp_model.CpModel()
        xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(self.problem.R) for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day)}

        for event_id in eset:
            model.Add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for room_id in range(self.problem.R)
                    for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day)
                ])==1
            )
        
        for event_id in eset:
            for room_id in range(self.problem.R):
                if room_id not in self.problem.event_available_periods[event_id]:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day)
                        ])==0
                    )
            
            for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day):
                if period_id not in self.problem.event_available_periods[event_id]:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(self.problem.R)
                        ])==0
                    )


        for room_id in range(self.problem.R):
            for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in eset
                    ])<=1
                )
        
        for event_id in eset:
            for neighbor_id in list(self.problem.G.neighbors(event_id)):
                if neighbor_id in eset:
                    for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day):
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])
                            +sum([
                                xvars[(neighbor_id,room_id,period_id)]
                                for room_id in range(self.problem.R)    
                            ])<=1
                        )
        
        if PRF.has_extra_constraints(self.problem.formulation):
            for event_id in eset:
                for event_id2 in self.problem.events[event_id]['HPE']:
                    if event_id2 in eset:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                                for period_id in range(day*self.problem.periods_per_day,day * self.problem.periods_per_day+self.problem.periods_per_day)
                            ])<sum([
                                xvars[(event_id2,room_id,period_id)]
                                for room_id in range(self.problem.R)
                                for period_id in range(day*self.problem.periods_per_day,day * self.problem.periods_per_day+self.problem.periods_per_day)
                            ])
                        )

        consecutive_events={ecombination:model.NewBoolVar(name=f'{"_".join(list([str(x) for x in ecombination]))}') for ecombination in event_combinations}

        for ecombination in event_combinations.keys():
            for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day-3):                    
                model.Add(
                    sum([
                        xvars[(event_id,room_id,pid)]
                        for event_id in ecombination
                        for room_id in range(self.problem.R)
                        for pid in range(period_id,period_id+3)
                    ])<=2+consecutive_events[ecombination]
                )
        
        objective=[
            sum([consecutive_events[ecombination] * no_students for ecombination,no_students in event_combinations.items()]),
            sum([xvars[(event_id,room_id,day * self.problem.periods_per_day+self.problem.periods_per_day-1)] * len(self.problem.events[event_id]['S']) for event_id in eset for room_id in range(self.problem.R)])
        ]
        
        model.Minimize(sum(objective))
        solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds=60
        solver.parameters.num_search_workers=os.cpu_count()
        solver.parameters.log_search_progress=True
        status=solver.Solve(model=model,solution_callback=cp_model.ObjectiveSolutionPrinter())
        
        if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
            for (event_id,room_id,period_id),dvar in xvars.items():
                if solver.Value(dvar)==1:
                    generated_solution[event_id]=(period_id,room_id)
        return generated_solution
    
    def days_combined(self,tsolver='cp-sat',days=[],solution_hint=True,timesol=600):
        generated_solution=dict()
        if tsolver=='cp-sat':
            model=cp_model.CpModel()
            eset=[event_id for event_id,sol_params in solution_hint.items() if sol_params['P']//self.problem.periods_per_day in days]
            periods=[period_id for day in days for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day)]
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(self.problem.R) for period_id in periods}
            partial_student_set=set([student_id for event_id in eset for student_id in self.problem.events[event_id]['S']])

            if solution_hint:
                for event_id in eset:
                    model.AddHint(xvars[(event_id,self.solution_set[event_id]['R'],self.solution_set[event_id]['P'])],1)

            for event_id in eset:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(self.problem.R)
                        for period_id in periods
                    ])==1
                )
            
            for event_id in eset:
                for room_id in range(self.problem.R):
                    if room_id not in self.problem.event_available_rooms[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for period_id in periods
                            ])==0
                        )
                for period_id in periods:
                    if period_id not in self.problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])==0
                        )
            
            for room_id in range(self.problem.R):
                for period_id in periods:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in eset
                        ])<=1
                    )

            for event_id in eset:
                for neighbor_id in list(self.problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in periods:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(self.problem.R)
                                ])+sum([
                                    xvars[(neighbor_id,room_id,period_id)]
                                    for room_id in range(self.problem.R)
                                ])<=1
                            )
            
            if PRF.has_extra_constraints(self.problem.formulation):
                for event_id in eset:
                    for event_id2 in self.problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]*period_id
                                    for room_id in range(self.problem.R)
                                    for period_id in periods
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]*period_id
                                    for room_id in range(self.problem.R)
                                    for period_id in periods
                                ])
                            )
                        else:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]*period_id
                                    for room_id in range(self.problem.R)
                                    for period_id in periods
                                ])<self.solution_set[event_id2]['P']
                            )
            
            single_event_days={(student_id,day):model.NewBoolVar(name=f'se_{student_id}_{day}') for student_id in partial_student_set for day in days}
            consecutive_events={(student_id,day,i):model.NewBoolVar(name=f'se_{student_id}_{day}_{i}') for student_id in partial_student_set for day in days for i in range(3,10)}

            for student_id in partial_student_set:
                student_events_set=[event_id for event_id in self.problem.students[student_id] if event_id in eset]
                for day in days:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in student_events_set
                            for room_id in range(self.problem.R)
                            for period_id in periods
                        ])==1
                    ).OnlyEnforceIf(single_event_days[(student_id,day)])

                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in student_events_set
                            for room_id in range(self.problem.R)
                            for period_id in periods
                        ])!=1
                    ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
                    
                    for i in range(3,10):
                        for period_id in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day-i+1):
                            previous_period_cost=0
                            next_period_cost=0
                            if period_id>day*self.problem.periods_per_day:
                                previous_period_cost=sum([xvars[(event_id,room_id,period_id-1)] for event_id in student_events_set for room_id in range(self.problem.R)])
                            if period_id<day*self.problem.periods_per_day+self.problem.periods_per_day-i-1:
                                next_period_cost=sum([xvars[(event_id,room_id,period_id+i)] for event_id in student_events_set for room_id in range(self.problem.R)])

                            model.Add(
                                previous_period_cost
                                -sum([
                                    xvars[(event_id,room_id,pid)]
                                    for event_id in student_events_set
                                    for room_id in range(self.problem.R)
                                    for pid in range(period_id,period_id+i)
                                ])
                                +next_period_cost
                                +consecutive_events[(student_id,day,i)]>=-(i-1)
                            )

            objective=[
                sum([single_event_days[(student_id,day)] for student_id in partial_student_set for day in days]),
                sum([consecutive_events[(student_id,day,i)]*(i-2) for student_id in partial_student_set for day in days for i in range(3,10)]),
                sum([xvars[(event_id,room_id,period_id)]*len(self.problem.events[event_id]['S']) for event_id in eset for room_id in range(self.problem.R) for period_id in [day*self.problem.periods_per_day+self.problem.periods_per_day-1 for day in days]])
            ]

            model.Minimize(sum(objective))
            solver=cp_model.CpSolver()
            solver.parameters.num_search_workers=os.cpu_count()
            solver.parameters.max_time_in_seconds=timesol
            solver.parameters.log_search_progress=True
            status=solver.Solve(model=model,solution_callback=cp_model.ObjectiveSolutionPrinter())
            if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1:
                        generated_solution[event_id]=(period_id,room_id)

            return generated_solution
    
    def solve_exact(self,solution_hint=True,timesol=600):
        generated_solution=dict()
        model=cp_model.CpModel()
        xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in range(self.problem.E) for room_id in range(self.problem.R) for period_id in range(self.problem.P)}

        # Add hint to the solution
        if solution_hint:
            for event_id,sol_vars in self.solution_set.items():
                model.AddHint(xvars[(event_id,sol_vars['R'],sol_vars['P'])],1)

        # Constraints
        for event_id in range(self.problem.E):
            model.Add(
                sum([xvars[(event_id,room_id,period_id)] for room_id in range(self.problem.R) for period_id in range(self.problem.P)])==1
            )
        
        for event_id in range(self.problem.E):
            for room_id in range(self.problem.R):
                if room_id in self.problem.event_available_rooms[event_id]:
                    continue
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)] for period_id in range(self.problem.P)
                    ])==0
                )
            if PRF.has_extra_constraints(self.problem.formulation):
                for period_id in range(self.problem.P):
                    if period_id not in self.problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(self.problem.R)
                            ])==1
                        )

        for room_id in range(self.problem.R):
            for period_id in range(self.problem.P):
                model.Add(
                    sum([xvars[(event_id,room_id,period_id)] for event_id in range(self.problem.E)])<=1
                )
        
        for event_id in range(self.problem.E):
            for event_id2 in self.problem.G.neighbors(event_id):
                for period_id in range(self.problem.P):
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for room_id in range(self.problem.R)])
                        +sum([xvars[(event_id2,room_id,period_id)] for room_id in range(self.problem.R)])
                        <=1
                    )
        
        if PRF.has_extra_constraints(self.problem.formulation):
            for period_id in range(self.problem.P):
                if period_id in self.problem.event_available_periods[event_id]:
                    continue
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)] for event_id in range(self.problem.E) for room_id in range(self.problem.R)
                    ])==0
                )

            for event_id in range(self.problem.E):
                for event_id2 in self.problem.events[event_id]['HPE']:
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(self.problem.R) for period_id in range(self.problem.P)])<
                        sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(self.problem.R) for period_id in range(self.problem.P)])
                    )
        
        single_event_days={(student_id,day):model.NewBoolVar(name=f'{student_id}_{day}') for student_id in range(self.problem.S) for day in range(self.problem.days)}
        consecutive_events={combination:model.NewBoolVar(name=f'ecombination_{combination}') for combination in self.problem.event_combinations}

        # Soft constraints 
        # 1. Single event days
        for student_id in range(self.problem.S):
            for day in range(self.problem.days):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in range(self.problem.E)
                        for room_id in range(self.problem.R)
                        for period_id in range(day * self.problem.periods_per_day,day * self.problem.periods_per_day+self.problem.periods_per_day)
                    ])==1
                ).OnlyEnforceIf(single_event_days[(student_id,day)])

                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in range(self.problem.E)
                        for room_id in range(self.problem.R)
                        for period_id in range(day * self.problem.periods_per_day,day * self.problem.periods_per_day+self.problem.periods_per_day)
                    ])!=1
                ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
        
        # 2. consecutive events
        for ecombination in self.problem.event_combinations:
            for day in range(self.problem.days):
                for pcons in range(day*self.problem.periods_per_day,day*self.problem.periods_per_day+self.problem.periods_per_day-3):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in ecombination
                            for room_id in range(self.problem.R)
                            for period_id in range(pcons,pcons+3)
                        ])<=2+consecutive_events[ecombination]
                    )
        
        objective=[
            sum([single_event_days[(student_id,day)] for student_id in range(self.problem.S) for day in range(self.problem.days)]),
            sum([consecutive_events[ecombination] * no_students for ecombination,no_students in self.problem.event_combinations.items()]),
            sum([xvars[(event_id,room_id,period_id)]*len(self.problem.events[event_id]['S']) for event_id in range(self.problem.E) for room_id in range(self.problem.R) for period_id in self.problem.last_period_per_day])
        ]

        model.Minimize(sum(objective))

        solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds=timesol
        solver.parameters.num_search_workers=os.cpu_count()
        solver.parameters.log_search_progress=True
        status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
        if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
            for (event_id,room_id,period_id),dvar in xvars.items():
                if solver.Value(dvar)==1:
                    generated_solution[event_id]=(period_id,room_id)
        
        return generated_solution


def room_solver(problem:Problem,solution_hint:dict,room:int,timesol=400):
    if solution_hint==None:
        raise ValueError("Please provide a solution hint in order to use the solver")
    
    model=cp_model.CpModel()
    eset=[event_id for event_id,sol_vars in solution_hint.items() if sol_vars['R']==room]

    xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in range(problem.P)}
    partial_students={student_id for event_id in eset for student_id in problem.events[event_id]['S']}
    shints=problem.create_hints(eset,solution_hint)
    ehints=problem.create_event_hints(eset,solution_hint)

    for event_id in eset:
        model.AddHint(xvars[(event_id,room_id,solution_hint[event_id]['R'],solution_hint[event_id]['P'])],1)

    for event_id in eset:
        model.Add(
            sum([
                xvars[(event_id,room_id,period_id)]
                for room_id in range(problem.R)
                for period_id in range(problem.P)
            ])==1
        )
    
    for event_id in eset:
        for room_id in range(problem.R):
            if room_id not in problem.event_available_rooms[event_id]:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for period_id in range(problem.P)
                    ])==0
                )
        for period_id in range(problem.P):
            if period_id not in problem.event_available_periods[event_id]:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                    ])==0
                )
    
    for room_id in range(problem.R):
        for period_id in range(problem.P):
            model.Add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for event_id in eset
                ])+sum([
                    ehints[event_id][(room_id,period_id)]
                    for event_id in range(problem.E)
                ])<=1
            )

    for event_id in eset:
        for event_id2 in problem.G.neighbors(event_id):
            if event_id2 in eset:
                for period_id in range(problem.P):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])
                        +sum([
                            xvars[(event_id2,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])<=1
                    )
            else:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,solution_hint[event_id2]['P'])]
                        for room_id in range(problem.R)
                    ])==0
                )
    
    if PRF.has_extra_constraints(problem.formulation):
        for event_id in eset:
            for event_id2 in problem.events[event_id]['HPE']:
                if event_id2 in eset:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]*period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])<sum([
                            xvars[(event_id2,room_id,period_id)]*period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])
                    )
                else:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])<solution_hint[event_id2]['P']
                    )

    single_event_days={(student_id,day):model.NewBoolVar(name=f'dv_{student_id}_{day}') for student_id in partial_students for day in range(problem.days)}
    consecutive_events={(student_id,day,i):model.NewBoolVar(name=f'dv_{student_id}_{day}_{i}') for student_id in partial_students for day in range(problem.days) for i in range(3,10)}

    for student_id in partial_students:
        for day in range(problem.days):
            partial_events_set=list(set(eset).intersection(set(problem.students[student_id])))
            model.Add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for event_id in partial_events_set
                    for room_id in range(problem.R)
                    for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                ])+sum([
                    shints[student_id][period_id]
                    for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                ])==1
            ).OnlyEnforceIf(single_event_days[(student_id,day)])

            model.Add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for event_id in partial_events_set
                    for room_id in range(problem.R)
                    for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                ])+sum([
                    shints[student_id][period_id]
                    for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                ])!=1
            ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
        
        for i in range(3,10):
            for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-i+1):
                previous_cost=0
                after_cost=0
                if period_id-1>day*problem.periods_per_day:
                    previous_cost=sum([xvars[(event_id,room_id,period_id-1)] for event_id in partial_events_set for room_id in range(problem.R)])+shints[student_id][period_id-1]
                elif period_id+i<day*problem.periods_per_day+problem.periods_per_day:
                    after_cost=sum([xvars[(event_id,room_id,period_id+i)] for event_id in partial_events_set for room_id in range(problem.R)])+shints[student_id][period_id+i]
                
                model.Add(
                    previous_cost
                    -sum([
                        xvars[(event_id,room_id,pid)]
                        for event_id in partial_events_set
                        for room_id in range(problem.R)
                        for pid in range(period_id,period_id+i)
                    ])
                    +after_cost
                    +consecutive_events[(student_id,day,i)]<=-(i-1)
                )
        
        objective=[
            sum([single_event_days[(student_id,day)] for student_id in partial_students for day in range(problem.days)]),
            sum([consecutive_events[(student_id,day,i)]*(i-2) for student_id in partial_students for day in range(problem.days) for i in range(3,10)]),
            sum([xvars[(event_id,room_id,period_id)] for event_id in eset for room_id in range(problem.R) for period_id in problem.last_period_per_day])
        ]

        model.Minimize(sum(objective))

        solver=cp_model.CpSolver()
        solver.parameters.max_time_in_seconds=timesol
        solver.parameters.num_search_workers=os.cpu_count()
        solver.parameters.log_search_progress=True
        status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter())
        if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
            generated_solution=dict()
            for (event_id,room_id,period_id),dvar in xvars.items():
                if solver.Value(dvar)==1:
                    generated_solution[event_id]=(period_id,room_id)
        return generated_solution