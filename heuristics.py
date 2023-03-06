from solution import Solution

class Hill_ClimbingLA:
    def __init__(self,dataset_name:str) -> None:
        self.solution=Solution(dataset_name)
    
    def solve(self):
        best_solution=self.solution.solution_set
        fitness=self.solution=self.solution.compute_cost()