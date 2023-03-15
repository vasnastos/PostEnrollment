from solution import Solution
from rich.console import Console
import random,time,math

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
            
            if time.time()-start_timer:
                console.print("[blue]Time stop criterio exceeded!!!")
                break

        return best_solution


class SimulatedAnnealing:
    def __init__(self,ds_name) -> None:
        self.solution=Solution(ds_name)
    
    def solve(self,temperature=1000,alpha=0.9999,timesol=1000):
        start_temperature=temperature
        ited_id=0
        start_timer=time.time()
        best_cost=self.cost
        best_solution=self.solution.solution_set
        freeze=1.0
        console=Console(record=True)

        while True:
            moves=self.solution.select_operator()
            if moves=={}:
                if time.time()-start_timer>timesol:
                    break
                continue
                
            self.solution.reposition(moves)
            previous_cost=self.cost
            if self.cost<best_cost:
                best_solution=self.solution.solution_set
                best_cost=self.cost
                console.print(f'[bold green]New solution found Cost:{best_cost}\tT:{temperature}')
            elif self.cost>best_cost:
                delta=self.cost-previous_cost
                if random.uniform(0,1)>math.exp(-delta/temperature):
                    pass
                else:
                    self.solution.rollback()
            
            iter_id+=1
            temperature*=alpha
            if temperature<freeze:
                temperature=start_temperature * random.uniform(0,2)
                console.print(f'[bold red]Temperature reheating:{temperature}')
            
            if time.time()-start_timer>timesol:
                break






