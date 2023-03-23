from rich.console import Console
import random,time,math,sys,copy,math
from queue import LifoQueue
from pe import Problem,Solution
from solvers import create_timetable,solve,SolverInfo
import os,pickle

class Hill_ClimbingLA:
    def __init__(self,dataset_name:str,initial_threshold:int) -> None:
        self.solution=Solution(dataset_name)
        self.current_age=0
        self.threshold=initial_threshold
        self.solution_distribution=dict()
    
    def solve(self,hcmax_age:int,timesol:int):
        max_age=hcmax_age
        best_solution=self.solution.solution_set
        console=Console(record=True)
        evalution_cost=self.solution.compute_cost()
        best_cost=evaluation_cost
        start_timer=time.time()

        while True:
            moves=self.solution.select_operator()
            ecost=self.solution.reposition(moves)
            previous_cost=evalution_cost
            evaluation_cost+=ecost
            delta=evaluation_cost-previous_cost
            
            if evalution_cost<best_cost:
                console.print(f'[bold green] New Solution found|Cost:{evaluation_cost}')

            elif evalution_cost>best_cost:
                if random.uniform(0,1) < min(1,(self.current_age+1)/max_age) * delta/self.threshold:
                    console.print(f'[bold red]Worse solution accepted| Cost:{evalution_cost}')
                    self.current_age=0
                else:
                    self.current_age+=1
                    self.solution.rollback()

            if self.current_age>max_age:
                self.current_age=0
                self.threshold*=2

            if self.threshold>=1e10:
                break 
            
            if time.time()-start_timer>timesol:
                console.print("[blue]Time stop criterio exceeded!!!")
                break

        return best_solution


class SimulatedAnnealing:
    def __init__(self,ds_name) -> None:
        self.solution=Solution(ds_name)
        self.console=Console(record=True)
    
    def preprocessing(self):
        instance=SolverInfo.get_instance()
        self.console.rule(f'Simulated Annealing - Initial Solution Constructed')
        init_sol=create_timetable(problem=self.solution.problem,csolver='gurobi',timesol=600)
        if init_sol!={}:
            self.solution.set_solution(init_sol)
        self.solution.validator()
        self.solution.save(filepath=os.path.join('','results','initial_solutions',f'{self.solution.problem.id}_{instance.get_solver_type()}.txt'))
        self.console.rule('Day by day Optimization')
        for i in range(self.solution.problem.days):
            self.console.print(f'Day by day improvement| Day:{i}\tCost:{self.solution.compute_daily_cost(i)}')
            init_sol=solve(problem=self.solution.problem,day_by_day=True,timesol=60,solution_hint=self.solution.solution_set,day=i)
            if init_sol!={}:
                self.solution.set_solution(init_sol)

        with open(os.path.join('','results','initial_solutions',f'{self.solution.problem.id}_{instance.get_solver_type()}_{self.solution.compute_cost()}.txt'),'w') as writer:
            for _,sol_params in self.solution.solution_set.items():
                writer.write(f'{sol_params["P"]} {sol_params["R"]}\n')

    def solve(self,temperature=1000,alpha=0.9999,timesol=1000):
        move_history=list()
        self.preprocessing()
        self.console.print(f'Initial Cost after preprocessing stage:{self.solution.cost}')
        self.console.print(f'Temperature:{temperature}')
        self.console.print(f'Alpha:{alpha}')
        self.console.print(f'Solution TimeLimit:{timesol+600+60*5}')
        instance=SolverInfo.get_instance()
        start_temperature=temperature
        start_timer=time.time()
        best_cost=self.solution.cost
        best_solution=self.solution.solution_set
        iter_id=0
        freeze=1.0

        while True:
            moves,move_name=self.solution.select_operator()
            if moves=={}:
                if time.time()-start_timer>timesol:
                    break
                continue
                
            self.solution.reposition(moves)

            previous_cost=self.solution.cost
            if self.solution.cost<best_cost:
                best_solution=self.solution.solution_set
                best_cost=self.solution.cost
                self.console.print(f'[bold green]New solution found Cost:{best_cost}\tT:{temperature}\tMove:{move_name}')
                move_history.append(move_name)
                iter_id+=1
            elif self.solution.cost>best_cost:
                delta=self.solution.cost-previous_cost
                if random.uniform(0,1)<math.exp(-delta/temperature):
                    # Solution will be accepted|Metropolis criterion
                    pass
                else:
                    self.solution.rollback()
                iter_id+=1
            else:
                iter_id+=1

            temperature*=alpha
            # if temperature<freeze:
            #     temperature=start_temperature * random.uniform(0,2)
            #     self.console.rule(f'[bold red]Temperature reheating:{temperature}')
            #     selection_criterion=random.uniform(0,1)

            #     if selection_criterion<0.3:
            #         daily_costs=list(sorted({day:self.solution.compute_daily_cost(day) for day in range(self.solution.problem.days)}.items(),key=lambda x:x[1]))
            #         partial_solution=solve(problem=self.solution.problem,day_by_day=True,solution_hint=self.solution.solution_set,timesol=50,day=daily_costs[0][0])
            #         if partial_solution!={}:
            #             self.solution.set_solution(partial_solution)
            #             best_solution=self.solution.solution_set
            #             best_cost=self.solution.cost
            #             self.console.print(f'[bold green]Best solution found| Solver:{instance.get_solution_info()}\tCost:{self.solution.cost}')

            #     else:
            #         daily_costs=list(sorted({day:self.solution.compute_daily_cost(day) for day in range(self.solution.problem.days)}.items(),key=lambda x:x[1]))
            #         days_combined_selection_number=random.randint(2,3)
            #         days=[daily_costs[i][0] for i in range(days_combined_selection_number)]
            #         partial_solution=solve(problem=self.solution.problem,days_combined=True,timesol=200,solution_hint=self.solution.solution_set,days=days)
            #         if partial_solution!={}:
            #             self.solution.set_solution(partial_solution)
            #             self.console.print(f'[bold green]New Solution generated\tSolver:{instance.get_solution_info()}\tDays feeded in solver:{days}\tCost:{self.solution.cost}')
            #             best_solution=self.solution.solution_set
            #             best_cost=self.solution.cost

            if time.time()-start_timer>timesol:
                self.console.print('Procedure ended!!! Exit Simulated Annealing')
                break
        self.solution.save(filepath=os.path.join('','results','simulated_annealing',f'{self.solution.problem.id}_{instance.get_solver_type()}_{self.solution.cost}.sol'))



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
        # event_id=random.choice(list(self.solution_set.keys()))
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