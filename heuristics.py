from rich.console import Console
import random,time,math
from pe import PRF
from solution import Solution
from solvers import create_timetable,solve
import os

class SimulatedAnnealing:
    def __init__(self,ds_name) -> None:
        self.solution=Solution(ds_name)
        self.console=Console(record=True)
        self.history=list()
    
    def preprocessing(self):
        self.console.rule(f'Simulated Annealing - Initial Solution Constructed')
        self.solution.create_timetable(tsolver='gurobi',timesol=1600)
        print(f'{self.solution.is_feasible()=}')

    def solve(self,temperature=1000,alpha=0.9999,timesol=1000):
        self.preprocessing()
        self.console.print(f'Initial Cost after preprocessing stage:{self.solution.cost}')
        self.console.print(f'Temperature:{temperature}')
        self.console.print(f'Alpha:{alpha}')
        self.console.print(f'Solution TimeLimit:{timesol+600+60*5}')
        start_temperature=temperature
        start_timer=time.time()
        best_cost=self.solution.compute_cost()
        best_solution=self.solution.solution_set
        iter_id=0
        freeze=1.0
        self.history.append(("INITIAL",best_cost))
        self.console.print(f'[bold green]SA| Initial Solution:{best_cost}')

        while True:
            moves,move_name=self.solution.select_operator()
            if moves=={}:
                if time.time()-start_timer>timesol:
                    break
                continue
            previous_cost=self.solution.compute_cost()
            self.solution.reposition(moves)
            current_cost=self.solution.compute_cost()
            self.history.append((move_name,current_cost))

            if current_cost<previous_cost:
                if current_cost<best_cost:
                    best_solution=self.solution.solution_set
                    best_cost=current_cost
                    self.console.print(f'[bold green]New solution found S:{best_cost}\tT:{temperature}\tMove:{move_name}')
                iter_id+=1
            elif current_cost>previous_cost:
                delta=current_cost-previous_cost
                if random.uniform(0,1)<math.exp(-delta/temperature):
                    # Solution will be accepted|Metropolis criterion
                    pass
                else:
                    self.solution.rollback()
                iter_id+=1
            else:
                iter_id+=1

            temperature*=alpha
            if temperature<freeze:
                temperature=start_temperature * random.uniform(0,2)
                self.console.rule(f'[bold red]Temperature reheating:{temperature}')
                selection_criterion=random.random()

                if selection_criterion<0.3:
                    daily_costs=list(sorted({day:self.solution.compute_daily_cost(day) for day in range(self.solution.problem.days)}.items(),key=lambda x:x[1],reverse=True))
                    partial_solution=self.solution.day_by_day(day=daily_costs[0][0])
                    if partial_solution!={}:
                        self.solution.set_solution(partial_solution)
                        new_cost=self.solution.compute_cost()
                        best_solution=self.solution.solution_set
                        best_cost=new_cost
                        self.console.print(f'[bold green]Best solution found| Solver:\tCost:{new_cost}')
                        self.history.append(('DBD',new_cost))
                else:
                    daily_costs=list(sorted({day:self.solution.compute_daily_cost(day) for day in range(self.solution.problem.days)}.items(),key=lambda x:x[1],reverse=True))
                    days_combined_selection_number=random.randint(2,3)
                    days=[daily_costs[i][0] for i in range(days_combined_selection_number)]
                    partial_solution=self.solution.days_combined(days=days,solution_hint=True,timesol=500)
                    if partial_solution!={}:
                        self.solution.set_solution(partial_solution)
                        new_cost=self.solution.compute_cost()
                        self.console.print(f'[bold green]New Solution generated\tSolver:\tDays feeded in solver:{days}\tCost:{new_cost}')
                        best_solution=self.solution.solution_set
                        best_cost=new_cost
                        self.history.append(('DC',new_cost))

            if time.time()-start_timer>timesol:
                self.console.print('Procedure ended!!! Exit Simulated Annealing')
                break
        
        print(f'{self.solution.is_feasible()=}')
        self.solution.set_solution(best_solution)
        self.solution.save(filepath=os.path.join('','results','simulated_annealing',f'{self.solution.problem.id}_{self.solution.compute_cost()}.sol'))
    
    def plot(self):
        pass