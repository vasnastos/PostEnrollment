# Number of events, number of rooms, number of features, number of students.
import os
from collections import defaultdict
import sys

def select_dataset():
    datasets=os.listdir(os.path.join(Problem.path_to_datasets))
    for i,ds_name in enumerate(datasets):
        print(f'{i+1}.{ds_name}')
    try:
        return datasets[int(input('Select dataset:'))-1]
    except ValueError:
        return "noname"

def import_problem(ds_name):
    with open(os.path.join(Problem.path_to_datasets,ds_name)) as RF:
        rooms=list()
        students=defaultdict(list)
        features=defaultdict(list)
        student_id=1
        feature_id=1
        count_after=0
        start=True
        for i,line in enumerate(RF):
            if i==0:
                events,roomsn,featuresn,studentsn=[int(x) for x in line.split()]
                continue
            if i<=roomsn:
                rooms.append(int(line))
                continue 
            if student_id==studentsn:
                if start:
                    start=False
                    count_after=0
                if count_after!=0 and count_after%featuresn==0:
                    feature_id+=1    
                features[feature_id].append(int(line))
                count_after+=1
            else:
                if count_after%events==0 and count_after!=0:
                    assert(len(students[student_id])==events)
                    student_id+=1
                students[student_id].append(int(line))          
                count_after+=1

    return Problem(events,roomsn,featuresn,studentsn,rooms,students,features)


class Problem:
    path_to_datasets=os.path.join('','instances')
    
    def __init__(self,E,R,F,S,rooms,students,features):
        self.events=E
        self.roomsn=R
        self.featuresn=F
        self.studentsno=S

        self.rooms=rooms  
        self.students=students
        self.features=features

    def __str__(self) -> str:
        msg=f'Events:{self.events},Rooms:{self.rooms},Features:{self.features},Students:{self.students}\n'
        for i,room in enumerate(self.rooms):
            msg+='Room:{i}\tCapacity:{room}\n'
        msg+='\n\n'
        for student,events in self.students.items():
            msg+=f'Student:{student}\t{"-".join([f"ev{i}:{ev}" for i,ev in enumerate(events)])}\n'
        for event,feats in self.features.items():
            msg+=f'Event:{event}:\t{"-".join([f"feature{i}:{f}" for i,f in enumerate(feats)])}\n'
        return msg

if __name__=='__main__':
    dataset=select_dataset()
    if dataset=="noname":
        sys.exit(0)
    p=import_problem(dataset)
    print(str(p))