from ortools.sat.python import cp_model
import docplex.cp.model as cpx
from pe import Problem,PRF
from solution import Solution
from queue import LifoQueue
import os,time,math,random,sys,copy
from itertools import combinations,product
from rich.console import Console
import gurobipy as gp

class TabuSearch:
    def __init__(self,filename):
        self.problem=Problem()
        self.problem.read(filename)
        self.solution_set={event_id:(-1,-1) for event_id in range(self.problem.E)}
        self.periodwise_solutions={period_id:list() for period_id in range(self.problem.P)}
    
    def modify(self,event_id,value,wise='period'):
        if wise=='period':
            self.solution_set[event_id]['P']=value
        elif wise=='room':
            self.solution_set[event_id]['R']=value

    def can_be_moved(self,wise='room',excluded=[],**kwargs):
        if wise=='room':
            if 'room' not in kwargs:
                raise ValueError("Room does not appear in kwargs")
            if 'period' not in kwargs:
                raise ValueError("Period does not appear in kwargs")
            
            room_id=int(kwargs['room'])
            period_id=int(kwargs['period'])

            for event_id in self.periodwise_solution[period_id]:
                if event_id in excluded: continue
                if self.solution_set[event_id]['R']==room_id:
                    return False
            return True
        
        elif wise=='period':
            if 'event' not in kwargs:
                raise ValueError("Room does not appear in kwargs")
            if 'period' not in kwargs:
                raise ValueError("Period does not appear in kwargs")

            event_id=int(kwargs['event'])
            period_id=int(kwargs['period'])

            for neighbor_id in list(self.problem.G.neighbors(event_id)):
                if period_id==self.solution_set[neighbor_id]['P']:
                    return False
            return True

        raise ValueError("You did not provide right argument type")

    def transfer(self,event_id):
        random.seed=int(time.time())
        shuffled_rooms=list(range(self.problem.R))
        random.shuffle(shuffled_rooms)

        event_id=list(self.solution_set.keys())[random.randint(0,len(list(self.solution_set.keys())))-1]

        for room_id in shuffled_rooms:
            if room_id in self.problem.event_available_rooms[event_id]:
                if self.can_be_moved(wise='room',room=room_id,period=self.solution_set[event_id]['P']):
                    return {
                        event_id:(self.solution_set[event_id]['P'],room_id)
                    }
                
    def swap(self,event_id):
        # event_id=list(self.solution_set.keys())[random.randint(0,len(list(self.solution_set.keys())))]
        event_id2=list(self.solution_set.keys())[random.randint(0,len(list(self.solution_set.keys())))]
        while event_id2==event_id:
            event_id2=list(self.solution_set.keys())[random.randint(0,len(list(self.solution_set.keys())))]
        if self.can_be_moved(wise='room',excluded=[event_id2],room=self.solution_set[event_id2]['R'],period=self.solution_set[event_id]['P']) and self.can_be_moved(wise='room',excluded=[event_id],room=self.solution_set[event_id]['R'],period=self.solution_set[event_id2]['P']):
            return {
                event_id:(self.solution_set[event_id]['P'],self.solution_set[event_id2]['R']),
                event_id2:(self.solution_set[event_id2]['P'],self.solution_set[event_id]['R'])
            }
        return dict()
    
    def kempe_chain(self,event_id):
        # event_id=list(self.solution_set.keys())[random.randint(0,len(list(self.solution_set.keys())))]
        event_id2=random.choice(self.problem.G.neighbors(event_id))

        versus_period={
            self.solution_set[event_id]['R']:self.solution_set[event_id2]['R'],
            self.solution_set[event_id2]['R']:self.solution_set[event_id]['R']
        }

        kc=LifoQueue()
        kc.put(event_id)
        moves={}
        while not kc.empty():
            current_event=kc.get()
            current_room=self.solution_set[current_event]['R']
            new_room=versus_period[current_room]
            moves[current_event]=new_room
            for neighbor_id in list(self.problem.G.neighbors(current_event)):
                if neighbor_id in moves: continue
                if self.solution_set[neighbor_id]['R']==new_room:
                    kc.put(neighbor_id)
        
        return moves

    def kick(self,event_id):
        event_id2=random.choice(list(self.solution_set.keys()))
        random.seed=int(time.time())
        shuffle_slots=self.problem.event_available_rooms[event_id2]
        random.shuffle(shuffle_slots)
        
        while event_id==event_id2:
            event_id2=random.choice(list(self.solution_set.keys()))
        
        if self.solution_set[event_id2]['R'] not in self.problem.event_available_rooms[event_id]:
            return dict()

        candicate_move=dict()
        if self.can_be_moved(wise='room',excluded=[event_id2],room=self.solution_set[event_id2]['R'],period=self.solution_set[event_id]['P']):
            candicate_move[event_id]=(self.solution_set[event_id]['P'],self.solution_set[event_id2]['R'])
        
        complete_kick_move=False
        for room_id in shuffle_slots:
            if room_id==self.solution_set[event_id2]['R']: continue
            if self.can_be_moved(wise='room',room=room_id,period=self.solution_set[event_id]['P']):
                candicate_move[event_id2]=(self.solution_set[event_id2]['P'],room_id)
                complete_kick_move=True
                break
        
        if complete_kick_move:
            return candicate_move
        return dict()


    def TS(self,tabu_size=500):
        unplacedE=list(range(self.solution.problem.E))
        current_solution={event_id:-1 for event_id in range(self.solution.problem.E)}
        current_best_solution=current_solution
        current_best_objective=sys.maxsize
        console=Console(record=True)
        tabu_list=list()
        memory=dict()
        start_timer=time.time()
        console.rule('[bold red] Tabu Search Initial Solution')
        obj=lambda unplacedE_val:len(unplacedE)

        while len(unplacedE)!=0:
            minimum_cost=sys.maxsize
            best_event=None
            best_slot=None
            unplacedE_copy=copy.copy(unplacedE)
            for event_id in unplacedE:
                unplacedE_copy.remove(event_id)
                for timeslot in self.solution.problem.event_available_periods[event_id]:
                    if self.solution.can_be_moved(event_id,timeslot,excluded=self.solution.problem.G.neighbors(event_id)):
                        memory.clear()
                        for neighbor_id in self.solution.problem.G.neighbors(event_id):
                            memory[neighbor_id]=(current_solution[neighbor_id],neighbor_id not in unplacedE)
                            current_solution.pop(neighbor_id)
                            if neighbor_id not in unplacedE_copy:
                                unplacedE_copy.append(neighbor_id)
                        
                        if obj(unplacedE)<minimum_cost and current_solution not in tabu_list:
                            best_event=event_id
                            best_slot=timeslot
                            minimum_cost=len(unplacedE_copy)
                        
                        for neighbor_id in self.solution.problem.G.neighbors(event_id):
                            current_solution[neighbor_id]=memory[neighbor_id][0]
                            if not memory[neighbor_id][1]:
                                unplacedE_copy.remove(neighbor_id)
                
                unplacedE_copy.append(event_id)
            
            if best_event:
                console.log(f'[bold green] New candicate Solution\tE{best_event}->P{best_slot} Objective:{minimum_cost}')
            
                for neighbor_id in self.solution.problem.neighbors(best_event):
                    if neighbor_id in current_solution:
                        current_solution.pop(neighbor_id)
                        unplacedE_copy.append(neighbor_id)
                
                if obj(unplacedE_copy)<current_best_objective:
                    current_best_objective=obj(unplacedE_copy)
                    current_solution[best_event]=best_slot
                    for neighbor_id in self.solution.problem.neighbors(best_event):
                        if neighbor_id in current_solution:
                            current_solution.pop(neighbor_id)
                    current_best_solution=current_solution

                if len(tabu_list)==tabu_size:
                    tabu_list.pop(0)
                tabu_list.append(current_solution)

            if time.time()-start_timer:
                break
        return current_solution

    def TSSP(self,best,unassignedE,timesol):
        console=Console(record=True)
        unplacedE=copy.copy(unassignedE)
        current_solution=copy.copy(best)
        obj=lambda unplacedE_val:sum([1+self.solution.problem.clashe(event_id)/self.solution.problem.total_clash for event_id in unplacedE_val])
        ITER=math.pow(self.solution.problem.R,3)
        memory=dict()
        tabu_list=list()
        i=0
        start_time=time.time()
        console.rule('[bold red]TSSP Procedure')
        while len(unplacedE)==0:
            sampleE=[unplacedE[random.randint(0,len(unplacedE)-1)] for _ in range(10)]
            min_unplaced_cost=sys.maxsize
            best_event=None
            best_timeslot=None
            
            for event_id in sampleE:
                for timeslot in self.solution.problem.event_available_periods[event_id]:
                    memory.clear()
                    for neighbor_id in list(self.solution.problem.G.neighbors(event_id)):
                        if neighbor_id in self.solution_set:
                            memory[neighbor_id]=current_solution[neighbor_id]
                            if neighbor_id in current_solution:
                                current_solution.pop(neighbor_id)
                            if neighbor_id not in unplacedE:
                                unplacedE.append(neighbor_id)
                    
                    if obj(current_solution.keys())<min_unplaced_cost:
                        best_event=event_id
                        best_timeslot=timeslot

                    for neighbor_id in list(self.solution.problem.G.neighbors(event_id)):
                        current_solution[neighbor_id]=memory[neighbor_id]
                        unplacedE.remove(neighbor_id)

                tabu_list.append(current_solution)
                unplacedE.append(event_id)
            
            if best_event:
                for event_id in self.solution.problem.G.neighbors(best_event):
                    if event_id in current_solution:
                        current_solution.pop(event_id)
                current_solution[best_event]=best_timeslot
                min_unplaced_cost=obj(current_solution.keys())

            if obj(current_solution.keys())<obj(best.keys()):
                best=current_solution
                unassignedE=unplacedE
            
            
            unplacedE.remove(best_event)
            for neighbor_id in self.solution.problem.G.neighbors(best_event):
                if neighbor_id not in unplacedE:
                    unplacedE.append(neighbor_id)
            
            i+=1
            if i==ITER:
                for event_id,period_id in current_solution.items():
                    self.modify(event_id,period_id,wise='period')
                
                self.Perturb()
                i=0
                tabu_list.clear() 
            if time.time()-start_time>timesol:
                break
    
    def Perturb(self):
        for event_id in list(self.solution_set.keys()):
            for _ in range(len(self.problem.event_available_rooms[event_id])):
                roperator=random.randint(1,4)
                if roperator==1:
                    self.transfer(event_id)
                elif roperator==2:
                    self.swap(event_id)
                elif roperator==3:
                    self.kempe_chain(event_id)
                elif roperator==4:
                    self.kick(event_id)

class HCLA:
    def __init__(self,ds_name) -> None:
        self.solution=Solution(ds_name)
        self.console=Console(record=True)

    def preprocessing(self):
        init_sol=create_timetable(problem=self.solution.problem,csolver='cp-sat',timesol=600)
        if init_sol!={}:
            self.solution.set_solution(init_sol)
            self.console.print(f'[bold green] Initial solution cost using gurobi solver:{self.solution.cost}')

        for day in range(self.solution.problem.days):
            partial_sol=solve(problem=self.solution.problem,tsolver='cp-sat',day_by_day=True,timesol=60,day=day)
            if partial_sol!={}:
                previous_day_cost=self.solution.compute_daily_cost(day)
                self.solution.set_solution(partial_sol)
                self.console.print(f'[bold]HCLA| Day by day Improvement| Solution Cost:{previous_day_cost}->{self.solution.compute_daily_cost(day)}')
        
        self.console.print(f'[bold green]New solution Cost:{self.solution.cost}')


    def solve(self,timesol):
        self.preprocessing()
        
        Bs=self.solution.solution_set
        Bc=self.solution.cost
        iter_id=0
        temperature=1000
        start_timer=time.time()

        while True:
            candicate_sol=self.solution.select_operator()
            previous_cost=self.solution.cost
            self.solution.reposition(candicate_sol)
            delta=self.solution.cost-previous_cost
            if self.solution.cost<previous_cost:
                if self.solution.cost<Bc:
                    Bs=self.solution.solution_set
                    Bc=self.solution.cost
                    self.console.print(f"HCLA |New solution found| S:{self.solution.cost}\tT:{temperature}")
            elif self.solution.cost>previous_cost:
                iter_id+=1
                if random.random()<math.exp(-delta*temperature):
                    # Solution accepted 
                    pass
                else:
                    self.solution.rollback()
            else:
                iter_id+=1
            
            if iter_id%1000000==0:
                number_of_days=random.randint(2,3)
                daily_costs={day:self.solution.compute_daily_cost(day) for day  in range(self.solution.problem.days)}
                sorted_daily_costs=list(sorted(daily_costs.items(),key=lambda x:x[1],reverse=True))

                days_checked=[sorted_daily_costs[i][0] for i in range(number_of_days)]
                timer=random.randint(200,500)
                partial_sol=solve(problem=self.solution.problem,days_combined=True,timesol=timer,days=days_checked)
                if partial_sol!={}:
                    self.solution.set_solution(partial_sol)
                    self.console.print(f'[bold green]HCLA| New solution found using DAYS_COMBINED_SOLVER| S:{self.solution.cost}')
                    Bs=self.solution.solution_set
                    Bc=self.solution.cost
        
            if time.time()-start_timer>timesol:
                break
        
        self.console.print(f'[bold green]HCLA| Procedurte ended| Best cost found:{Bc}')
        return Bs

def create_timetable(problem:"Problem",csolver='cp-sat',timesol=600):
    """
        Initial solution creator. It constructs 3 different solutions using 3 different models(cp-sat,cplex-Cp and gurobi-mip)
        Parameters:
            - problem: A problem instance load by class Problem
            - csolver: The type of the solver is used for consructing initial solutions("cp-sat","cp-cplex","gurobi")
            - save: Format that the solution could be potential saved("txt","pickle","None")
            - timesol: time in seconds the the solver would run for
        Returns:
            - dict: contains the generated timetable
    """

    generated_solution={}
    if csolver=='cp-sat':
        model=cp_model.CpModel()
        xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}

        # 1. One event should be placed in only one room in only one period
        for event_id in range(problem.E):
            model.Add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for room_id in range(problem.R)
                    for period_id in range(problem.P)
                ])==1
            )
        
        # 2. Events should not be placed in non valid rooms or periods
        for event_id in range(problem.E):
            for room_id in range(problem.R):
                if room_id not in problem.event_available_rooms[event_id]:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
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

        # 3. One event should be schedule at each period-room pair
        for room_id in range(problem.R):
            for period_id in range(problem.P):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in range(problem.E)
                    ])<=1
                )


        # 4. Add neighborhood constraints
        for event_id in range(problem.E):
            for neighbor_id in list(problem.G.neighbors(event_id)):
                for period_id in range(problem.P):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])+sum([
                            xvars[(neighbor_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])<=1
                    )

        # 5. Add precedence relations
        if PRF.has_extra_constraints(problem.formulation):
            for event_id in range(problem.E):
                for event_id2 in problem.events[event_id]['HPE']:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])<sum([
                            xvars[(event_id2,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
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
    
    elif  csolver=="cp-cplex":
        # cplex solver
        model=cpx.CpoModel(name='post_enrollment_timetable_constructor')
        xvars={(event_id,room_id,period_id):model.binary_var(name={f"sd_{event_id}_{room_id}_{period_id}"}) for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}

        for event_id in range(problem.E):
            model.add(
                sum([
                    xvars[(event_id,room_id,period_id)]
                    for room_id in range(problem.R)
                    for period_id in range(problem.P)
                ])==1
            )
        
        # 2. Events should not be placed in non valid rooms or periods
        for event_id in range(problem.E):
            for room_id in range(problem.R):
                if room_id not in problem.event_available_rooms[event_id]:
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])==0
                    )
            
            for period_id in range(problem.P):
                if period_id not in problem.event_available_periods[event_id]:
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])==0
                    )

        # 3. One event should be schedule at each period-room pair
        for room_id in range(problem.R):
            for period_id in range(problem.P):
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for event_id in range(problem.E)
                    ])<=1
                )


        # 4. Add neighborhood constraints
        for event_id in range(problem.E):
            for neighbor_id in problem.G.neighbors(event_id):
                for period_id in range(problem.P):
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])+sum([
                            xvars[(neighbor_id,room_id,period_id)]
                            for room_id in range(problem.R)
                        ])<=1
                    )

        
        # 5. Add precedence relations
        if PRF.has_extra_constraints(problem.formulation):
            for event_id in range(problem.E):
                for event_id2 in problem.events[event_id]['HPE']:
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
                        ])<sum([
                            xvars[(event_id2,room_id,period_id)] * period_id
                            for room_id in range(problem.R)
                            for period_id in range(problem.P)
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


    elif csolver=='gurobi':
        # Gurobi solver
        model=gp.Model(name="Gurobi_post_enrollment")
        xvars=model.addVars([(event_id,room_id,period_id) for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)],vtype=gp.GRB.BINARY,name='xvars')

        for event_id in range(problem.E):
            model.addConstr(
                xvars.sum(event_id,'*','*')==1,name=f'Constr_{event_id}'
            )
        
        for event_id in range(problem.E):
            for room_id in range(problem.R):
                if room_id not in problem.event_available_rooms[event_id]:
                    model.addConstr(
                        xvars.sum(event_id,room_id,'*')==0
                    )
        
            for period_id in range(problem.P):
                if period_id not in problem.event_available_periods[event_id]:
                    model.addConstr(
                        xvars.sum(event_id,'*',period_id)==0,name=f'Period_Constr_{event_id}'
                    )
        
        for room_id in range(problem.R):
            for period_id in range(problem.P):
                model.addConstr(
                    xvars.sum('*',room_id,period_id)<=1,name=f'room_period_Constr_({room_id},{period_id})'
                )
        
        for event_id in range(problem.E):
            for event_id2 in problem.G.neighbors(event_id):
                for period_id in range(problem.P):
                    model.addConstr(
                        xvars.sum(event_id,'*',period_id)
                        +xvars.sum(event_id2,'*',period_id)<=1
                    )
        if PRF.has_extra_constraints(problem.formulation):
            for event_id in range(problem.E):
                for event_id2 in problem.events[event_id]['HPE']:
                    model.addConstr(
                        sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(problem.P)])<
                        sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(problem.P)])
                    )
        
        model.Params.TimeLimit=timesol
        model.Params.Threads=os.cpu_count()
        model.optimize()

        if model.Status in [gp.GRB.OPTIMAL,not gp.GRB.INFEASIBLE]:
            for (event_id,room_id,period_id),decision_var in xvars.items():
                if decision_var.X==1:
                    generated_solution[event_id]=(period_id,room_id)

    return generated_solution


def solve(problem:"Problem",tsolver='cp-sat',day_by_day=False,days_combined=False,full=False,timesol=600,**kwargs):
    generated_solution=dict()

    if sum([day_by_day,full,days_combined])==0:
        raise ValueError("Both day_by_day and full params setted to False.\n You should set one of the parameters in True")
    elif sum([day_by_day,full,days_combined])>1:
        raise ValueError("You set day_by_day and full solver to True. You must select one of the solvers to use")


    if full:
        if tsolver=='cp-sat':
            model=cp_model.CpModel()
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}
            
            solution_hint=None
            if 'solution_hint' in kwargs:
                solution_hint=kwargs['solution_hint']

            # Add hint to the solution
            if solution_hint:
                for event_id,(period_id,room_id) in solution_hint.items():
                    model.AddHint(xvars[(event_id,room_id,period_id)],1)

            # Constraints
            for event_id in range(problem.E):
                model.Add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(problem.P)])==1
                )
            
            for event_id in range(problem.E):
                for room_id in range(problem.R):
                    if room_id in problem.event_available_rooms[event_id]:
                        continue
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)] for period_id in range(problem.P)
                        ])==0
                    )

            for room_id in range(problem.R):
                for period_id in range(problem.P):
                    model.Add(
                        sum([xvars[(event_id,room_id,period_id)] for event_id in range(problem.E)])
                        <=1
                    )
            
            for event_id in range(problem.E):
                for event_id2 in problem.G.neighbors(event_id):
                    for period_id in range(problem.P):
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])
                            +sum([xvars[(event_id2,room_id,period_id)] for room_id in range(problem.R)])
                            <=1
                        )
            
            if PRF.has_extra_constraints(problem.formulation):
                for period_id in range(problem.P):
                    if period_id in problem.event_available_periods[event_id]:
                        continue
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)] for event_id in range(problem.E) for room_id in range(problem.R)
                        ])==0
                    )

                for event_id in range(problem.E):
                    for event_id2 in problem.events[event_id]['HPE']:
                        model.Add(
                            sum([xvars[(event_id,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(problem.P)])<
                            sum([xvars[(event_id2,room_id,period_id)]*period_id for room_id in range(problem.R) for period_id in range(problem.P)])
                        )
            
            single_event_days={(student_id,day):model.NewBoolVar(name=f'{student_id}_{day}') for student_id in range(problem.S) for day in range(problem.days)}
            consecutive_events={combination:model.NewBoolVar(name=f'ecombination_{combination}') for combination in problem.event_combinations}

            # Soft constraints 
            # 1. Single event days
            for student_id in range(problem.S):
                for day in range(problem.days):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in range(problem.E)
                            for room_id in range(problem.R)
                            for period_id in range(day * problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                        ])==1
                    ).OnlyEnforceIf(single_event_days[(student_id,day)])

                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in range(problem.E)
                            for room_id in range(problem.R)
                            for period_id in range(day * problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                        ])!=1
                    ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
            
            # 2. consecutive events
            for ecombination in problem.event_combinations:
                for day in range(problem.days):
                    for pcons in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-3):
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for event_id in ecombination
                                for room_id in range(problem.R)
                                for period_id in range(pcons,pcons+3)
                            ])<=2+consecutive_events[ecombination]
                        )
            
            objective=[
                sum([single_event_days[(student_id,day)] for student_id in range(problem.S) for day in range(problem.days)]),
                sum([consecutive_events[ecombination] * no_students for ecombination,no_students in problem.event_combinations.items()]),
                sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in range(problem.E) for room_id in range(problem.R) for period_id in problem.last_period_per_day])
            ]

            model.Minimize(sum(objective))

            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=timesol
            solver.parameters.num_search_workers=os.cpu_count()
            status=solver.Solve(model,cp_model.ObjectiveSolutionPrinter)
            if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1:
                        generated_solution[event_id]=(period_id,room_id)
    
    elif day_by_day:
        if 'day' not in kwargs:
            raise ValueError("Day-by-Day solver called and no day provided")
        if 'solution_hint' not in kwargs:
            raise ValueError("No initial solution provided")
        
        day=int(kwargs['day'])
        solution_hint=kwargs['solution_hint']
        eset=[event_id for event_id,sol_params in solution_hint.items() if sol_params['P']//problem.periods_per_day==day]
        event_combinations={frozenset(ecombination):problem.event_combinations[frozenset(ecombination)] for ecombination in combinations(eset,3) if frozenset(ecombination) in problem.event_combinations}

        if tsolver=='cp-sat':
            model=cp_model.CpModel()
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)}

            for event_id in eset:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                    ])==1
                )
            
            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id not in problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                            ])==0
                        )
                
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    if period_id not in problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(problem.R)
                            ])==0
                        )


            for room_id in range(problem.R):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in eset
                        ])<=1
                    )
            
            for event_id in eset:
                for neighbor_id in list(problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                ])
                                +sum([
                                    xvars[(neighbor_id,room_id,period_id)]
                                    for room_id in range(problem.R)    
                                ])<=1
                            )
            
            if PRF.has_extra_constraints(problem.formulation):
                for event_id in eset:
                    for event_id2 in problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(day*problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(day*problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                                ])
                            )

            consecutive_events={ecombination:model.NewBoolVar(name=f'{"_".join(list([str(x) for x in ecombination]))}') for ecombination in event_combinations}

            for ecombination in event_combinations.keys():
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-3):                    
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,pid)]
                            for event_id in ecombination
                            for room_id in range(problem.R)
                            for pid in range(period_id,period_id+3)
                        ])<=2+consecutive_events[ecombination]
                    )
            
            objective=[
                sum([consecutive_events[ecombination] * no_students for ecombination,no_students in event_combinations.items()]),
                sum([xvars[(event_id,room_id,day * problem.periods_per_day+problem.periods_per_day-1)] * len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R)])
            ]
            
            model.Minimize(sum(objective))
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=timesol
            solver.parameters.num_search_workers=os.cpu_count()
            # solver.parameters.log_search_progress=True
            status=solver.Solve(model=model,solution_callback=cp_model.ObjectiveSolutionPrinter())
            
            if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver.Value(dvar)==1:
                       generated_solution[event_id]=(period_id,room_id)

        elif tsolver=='cplex':
            model=cpx.CpoModel(name='cplex_post_enrollment')
            xvars={(event_id,room_id.period_id):model.binary_var(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)}     

            for event_id in eset:
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                    ])==1
                )
            
            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id in problem.event_available_periods[event_id]:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)
                            ])==0
                        )
                
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    if period_id not in problem.event_available_periods[event_id]:
                        model.add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(problem.R)
                            ])==0
                        )


            for room_id in range(problem.R):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    model.add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in eset
                        ])<=1
                    )
            
            for event_id in eset:
                for neighbor_id in list(problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                            model.add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                ])
                                +sum([
                                    xvars[(neighbor_id,room_id,period_id)]
                                    for room_id in range(problem.R)    
                                ])<=1
                            )
            
            if PRF.has_extra_constraints(problem.formulation):
                for event_id in eset:
                    for event_id2 in problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(problem.P)
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(day*problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                                ])
                            )

            consecutive_events={ecombination:model.binary_var(name=f'{"_".join(list(ecombination))}') for ecombination in event_combinations}

            for ecombination in consecutive_events.keys():
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-3):
                    model.add(
                        sum([
                            xvars[(event_id,room_id,pid)]
                            for event_id in ecombination
                            for room_id in range(problem.R)
                            for pid in range(period_id,period_id+3)
                        ])<=2+consecutive_events[ecombination]
                    )
            
            objective=[
                sum([consecutive_events[ecombination] * no_students for ecombination,no_students in event_combinations.items()]),
                sum([xvars[(event_id,room_id,day * problem.periods_per_day+problem.periods_per_day-1)] * len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R)])
            ]
            
            model.minimize(sum(objective))
            params=cpx.CpoParameters()
            params.Workers=os.cpu_count()
            params.TimeLimit=timesol
            params.LogVerbosity=True
            solver=model.solve(params=params)
            if solver:
                for (event_id,room_id,period_id),dvar in xvars.items():
                    if solver[dvar]==1:
                       generated_solution[event_id]=(period_id,room_id)
        
        elif tsolver=='gurobi':
            model=gp.Model()
            xvars=model.addVars(list(product(*[eset,list(range(problem.R)),list(range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day))])),name=f'decision_variables_post',vtype=gp.GRB.BINARY)

            for event_id in eset:
                model.addConstr(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in range(problem.P)
                    ])==1,name=f'EC1_{event_id}'
                )
            
            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id in problem.event_available_periods[event_id]:
                        model.addConstr(
                            xvars.sum(event_id,room_id,'*')==0,name=f'EC2_{event_id}_{room_id}_{period_id}'
                        )
                
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    if period_id not in problem.event_available_periods[event_id]:
                        model.addConstr(
                            xvars.sum(event_id,'*',period_id)==0,name=f'EC3_{period_id}'
                        )


            for room_id in range(problem.R):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                    model.addConstr(
                        xvars.sum('*',room_id,period_id)<=1,name=f'EC4_{room_id}_{period_id}'
                    )
            
            for event_id in eset:
                for neighbor_id in list(problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day):
                            model.add(
                                xvars.sum(event_id,'*',period_id)
                                +xvars.sum(neighbor_id,'*',period_id)<=1,name=f'EC5_{event_id}_{neighbor_id}_{period_id}'
                            )
            
            if PRF.has_extra_constraints(problem.formulation):
                for event_id in eset:
                    for event_id2 in problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.addConstr(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(problem.P)
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]
                                    for room_id in range(problem.R)
                                    for period_id in range(day*problem.periods_per_day,day * problem.periods_per_day+problem.periods_per_day)
                                ]),name=f'EC6_{event_id}_{event_id2}'
                            )
            
            consecutive_events=model.addVars(list(product(*[eset,list(range(problem.R)),list(range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day))])),name=f'secondary_variables',vtype=gp.GRB.BINARY)
            for ecombination in list(event_combinations.keys()):
                for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-3):
                    model.addConstr(
                        sum([
                            xvars[(event_id,room_id,pid)].V
                            for event_id in list(ecombination)
                            for room_id in range(problem.R)
                            for pid in range(period_id,period_id+3)
                        ])<2+consecutive_events[ecombination]
                    )
            
            objective=[
                sum([consecutive_events[ecombination] * no_students for ecombination,no_students in event_combinations.items()]),
                sum([xvars[(event_id,room_id,day*problem.periods_per_day+problem.periods_per_day-1)] for event_id in eset for room_id in range(problem.R)])
            ]

            model.setObjective(sum(objective))
            model.optimize()

            for (event_id,room_id,period_id),dvar in xvars.items():
                if dvar.X==1:
                    generated_solution[event_id]=(period_id,room_id)
    
    elif days_combined:
        if 'days' not in kwargs:
            raise ValueError("You did not provide the right amount of arguments in the solver")
        days=kwargs['days']
        
        if 'solution_hint' not in kwargs:
            solution_hint=None
        else:
            solution_hint=kwargs['solution_hint']

        if tsolver=='cp-sat':
            model=cp_model.CpModel()
            eset=[event_id for event_id,sol_params in solution_hint.items() if sol_params['P']//problem.periods_per_day in days]
            periods=[period_id for day in days for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day)]
            xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'dv_{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in periods}
            partial_student_set=set([student_id for event_id in eset for student_id in problem.events[event_id]['S']])

            if solution_hint:
                for event_id in eset:
                    model.AddHint(xvars[(event_id,solution_hint[event_id]['R'],solution_hint[event_id]['P'])],1)

            for event_id in eset:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                        for period_id in periods
                    ])==1
                )
            
            for event_id in eset:
                for room_id in range(problem.R):
                    if room_id not in problem.event_available_rooms[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for period_id in periods
                            ])==0
                        )
                for period_id in periods:
                    if period_id not in problem.event_available_periods[event_id]:
                        model.Add(
                            sum([
                                xvars[(event_id,room_id,period_id)]
                                for room_id in range(problem.R)
                            ])==0
                        )
            
            for room_id in range(problem.R):
                for period_id in periods:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in eset
                        ])<=1
                    )

            for event_id in eset:
                for neighbor_id in list(problem.G.neighbors(event_id)):
                    if neighbor_id in eset:
                        for period_id in periods:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                ])+sum([
                                    xvars[(neighbor_id,room_id,period_id)]
                                    for room_id in range(problem.R)
                                ])<=1
                            )
            
            if PRF.has_extra_constraints(problem.formulation):
                for event_id in eset:
                    for event_id2 in problem.events[event_id]['HPE']:
                        if event_id2 in eset:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]*period_id
                                    for room_id in range(problem.R)
                                    for period_id in periods
                                ])<sum([
                                    xvars[(event_id2,room_id,period_id)]*period_id
                                    for room_id in range(problem.R)
                                    for period_id in periods
                                ])
                            )
                        else:
                            model.Add(
                                sum([
                                    xvars[(event_id,room_id,period_id)]*period_id
                                    for room_id in range(problem.R)
                                    for period_id in periods
                                ])<solution_hint[event_id2]['P']
                            )
            
            single_event_days={(student_id,day):model.NewBoolVar(name=f'se_{student_id}_{day}') for student_id in partial_student_set for day in days}
            consecutive_events={(student_id,day,i):model.NewBoolVar(name=f'se_{student_id}_{day}_{i}') for student_id in partial_student_set for day in days for i in range(3,10)}

            for student_id in partial_student_set:
                student_events_set=[event_id for event_id in problem.students[student_id] if event_id in eset]
                for day in days:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in student_events_set
                            for room_id in range(problem.R)
                            for period_id in periods
                        ])==1
                    ).OnlyEnforceIf(single_event_days[(student_id,day)])

                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]
                            for event_id in student_events_set
                            for room_id in range(problem.R)
                            for period_id in periods
                        ])!=1
                    ).OnlyEnforceIf(single_event_days[(student_id,day)].Not())
                    
                    for i in range(3,10):
                        for period_id in range(day*problem.periods_per_day,day*problem.periods_per_day+problem.periods_per_day-i+1):
                            previous_period_cost=0
                            next_period_cost=0
                            if period_id>day*problem.periods_per_day:
                                previous_period_cost=sum([xvars[(event_id,room_id,period_id-1)] for event_id in student_events_set for room_id in range(problem.R)])
                            if period_id<day*problem.periods_per_day+problem.periods_per_day-i-1:
                                next_period_cost=sum([xvars[(event_id,room_id,period_id+i)] for event_id in student_events_set for room_id in range(problem.R)])

                            model.Add(
                                previous_period_cost
                                -sum([
                                    xvars[(event_id,room_id,pid)]
                                    for event_id in student_events_set
                                    for room_id in range(problem.R)
                                    for pid in range(period_id,period_id+i)
                                ])
                                +next_period_cost
                                +consecutive_events[(student_id,day,i)]>=-(i-1)
                            )

            objective=[
                sum([single_event_days[(student_id,day)] for student_id in partial_student_set for day in days]),
                sum([consecutive_events[(student_id,day,i)]*(i-2) for student_id in partial_student_set for day in days for i in range(3,10)]),
                sum([xvars[(event_id,room_id,period_id)]*len(problem.events[event_id]['S']) for event_id in eset for room_id in range(problem.R) for period_id in [day*problem.periods_per_day+problem.periods_per_day-1 for day in days]])
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



