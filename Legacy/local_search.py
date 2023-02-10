from Legacy.pe import Problem,Solution
import logging
from datetime import datetime
from time import time

class LocalSearch:
    def __init__(self,ds_name):
        self.problem=Problem(ds_name)
        self.solution=Solution(ds_name.replace('.tim',''))
    
    def simulated_annealing(self):
        logger=logging.getLogger(name='SA_post_enrollment')
        logger.setLevel(logging.INFO)
        formatter=logging.Formatter(fmt='%(asctime)s\t%(message)s')
        fh=logging.FileHandler(filename=f'SA_postenrollment_filehandler_{datetime.now().strftime("%Y_%m_%d____%H_%M_%S")}',mode='w')
        sh=logging.StreamHandler()
        logger.addHandler(fh)
        logger.addHandler(sh)
        sh.setFormatter(formatter)
        fh.setFormatter(formatter)
        logger.addHandler(sh)
        logger.addHandler(fh)

        temperature,start_temperature=1000,1000
        alpha=0.9999
        freeze_temp=1.0
        start_timer=time()
        # Best cost and solution initialization

        while True:
            pass
