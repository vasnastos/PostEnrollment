from solution import Solution
from rich.console import Console

class Hill_ClimbingLA:
    def __init__(self,dataset_name:str,initial_threshold:int) -> None:
        self.solution=Solution(dataset_name)
        self.current_age=0
        self.threshold=initial_threshold
    
    def solve(self,hcmax_age:int):
        max_age=hcmax_age
        best_solution=self.solution.solution_set
        best_cost=self.solution=self.solution.compute_cost()
        console=Console(record=True)

        while True:
            moves=self.solution.select_operator()