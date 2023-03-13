from solution import Solution
from rich.console import Console
import random,time

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
    def __init__(self) -> None:
        pass
    
    def solve(self,temperature=1000,alpha=0.9999,timesol=1000):
        pass


