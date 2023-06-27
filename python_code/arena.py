import os,pandas as pd

class Arena:
    path_to_arena=os.path.join('','results','arena')
    def __init__(self):
        nums=[0]+[int(filename.removesuffix('.csv').split('_')[1]) for filename in [x  for x in os.listdir(Arena.path_to_arena) if x.startswith('arena')]]
        self.id=max(nums)+1
        self.results=list()

    def add(self,dataset_id,events,rooms,density,cost):
        self.results.append(dataset_id,events,rooms,density,cost)
    
    def save(self):
        pd.DataFrame(data=[vals for vals in self.results],columns=['Dataset','Events','Rooms','Density','Cost']).to_csv(path_or_buf=os.path.join('','results','arena',f'arena_{self.id}.csv'),mode='w')
    
