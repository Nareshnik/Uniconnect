import random
from enum import Enum
from functools import lru_cache
from math import ceil
from statistics import mean
from typing import NamedTuple

import numpy as np
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
import random


def compare_timetable(t1, t2):
    for day in range(6):
        for period in range(7):
            try:
                # print(t1[day][period], t2[day][period])
                if("Free" not in t1[day][period]):
                    if t1[day][period] == t2[day][period]:
                        print("Clash Found")
                        
                        return 1
            except:
                # print(day, period)
                break
    
    return 0


class Subject:
    def __init__(self, name, numbers):
        self.name = name
        self.numbers = numbers

    def __repr__(self):
        return self.name


class SubjectType(Enum):
    LECTURE = 0
    SEMINAR = 1


class WeekDay(Enum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


C1 = 2  # uniformity
C2 = 0  # tightness
C3 = 1  # suitability
C4 = 0.1  # sleep
C5 = 0 # day_grouping
C6 = 0  # week_grouping

CLASSES_PER_DAY = 7
WORKING_DAYS = 6
PLACES = CLASSES_PER_DAY * WORKING_DAYS
SUBJECTS = []
SUITABLE_TIME = []

def set_subjects(subject_details):
    global SUBJECTS
    SUBJECTS = []
    for subject in subject_details:
        SUBJECTS.append(Subject(name=subject[0], numbers={SubjectType.LECTURE: int(subject[1]), SubjectType.SEMINAR: int(subject[2])}))

    # SUBJECTS = [
    #     Subject(name='S1', numbers={SubjectType.LECTURE: 4, SubjectType.SEMINAR: 2}),
    #     Subject(name='S2', numbers={SubjectType.LECTURE: 4, SubjectType.SEMINAR: 2}),
    #     Subject(name='S3', numbers={SubjectType.LECTURE: 4, SubjectType.SEMINAR: 1}),
    #     Subject(name='S4', numbers={SubjectType.LECTURE: 4, SubjectType.SEMINAR: 2}),
    #     Subject(name='S5', numbers={SubjectType.LECTURE: 4, SubjectType.SEMINAR: 1}),
    #     Subject(name='S6', numbers={SubjectType.LECTURE: 2, SubjectType.SEMINAR: 1}),
    #     Subject(name='S7', numbers={SubjectType.LECTURE: 2, SubjectType.SEMINAR: 1}),
    #     Subject(name='S8', numbers={SubjectType.LECTURE: 2, SubjectType.SEMINAR: 1}),
    #     Subject(name='S9', numbers={SubjectType.LECTURE: 2, SubjectType.SEMINAR: 1}),
    # ]

def set_suitable_timing():
    global SUITABLE_TIME
    SUITABLE_TIME = {
        WeekDay.MON: {1: [random.choice(SUBJECTS).name], 2: [], 3: [], 4: [], 5:[], 6:[], 7:[]},
        WeekDay.TUE: {1: [], 2: [], 3: [], 4: [], 5:[], 6:[], 7:[]},
        WeekDay.WED: {1: [random.choice(SUBJECTS).name], 2: [], 3: [], 4: [], 5:[], 6:[], 7:[]},
        WeekDay.THU: {1: [], 2: [], 3: [], 4: [], 5:[], 6:[], 7:[]},
        WeekDay.FRI: {1: [random.choice(SUBJECTS).name], 2: [], 3: [], 4: [], 5:[], 6:[], 7:[]},
        WeekDay.SAT: {1: [], 2: [], 3: [], 4: [], 5:[], 6:[], 7:[]}
    }
    
    # SUITABLE_TIME = {
    #     WeekDay.MON: {1: ['S1'], 2: [], 3: [], 4: [], 5:[], 6:[], 7:[]},
    #     WeekDay.TUE: {1: ['S2'], 2: ['PR'], 3: ['PR'], 4: [], 5:[], 6:[], 7:[]},
    #     WeekDay.WED: {1: ['S4,S3'], 2: ['AG'], 3: ['MA'], 4: [], 5:[], 6:[], 7:[]},
    #     WeekDay.THU: {1: ['DM'], 2: ['EN'], 3: ['MA', 'EN'], 4: [], 5:[], 6:[], 7:[]},
    #     WeekDay.FRI: {1: ['MA'], 2: ['DM'], 3: [], 4: [], 5:[], 6:[], 7:[]},
    #     WeekDay.SAT: {1: ['MA'], 2: ['DM'], 3: ['MA'], 4: [], 5:[], 6:[], 7:[]}
    # }


class Class(NamedTuple):
    subject: Subject
    type: SubjectType


# for better performance
def diff(x):
    return [b - a for a, b in zip(x[:-1], x[1:])]


@lru_cache(maxsize=None)
def calc_uniformity(num_by_day):
    n = sum(num_by_day)
    p = WORKING_DAYS
    mean_num = n / p

    # for 14: 3 3 3 3 2
    min_dev = (p - n % p) * (mean_num - n // p) + \
              (n % p) * (n // p + 1 - mean_num)
    # stack all classes one after other i.e. for 14: 4 4 4 2 0
    max_dev = ((n // CLASSES_PER_DAY) * (CLASSES_PER_DAY - mean_num) +
               abs(n % CLASSES_PER_DAY - mean_num) +
               (p - ceil(n / CLASSES_PER_DAY)) * mean_num)
    dev = sum(abs(c - mean_num) for c in num_by_day)
    return 1 - (dev - min_dev) / (max_dev - min_dev)


def first_non_none(lst):
    return next(i for i, class_ in enumerate(lst) if class_ is not None)


def construct_schedule(ordering, mapping):
    classes_num = len(mapping)
    subjects_ordering = [mapping[o] if o < classes_num else None for o in ordering]
    return [subjects_ordering[i:i + CLASSES_PER_DAY] for i in range(0, len(subjects_ordering), CLASSES_PER_DAY)]


def eval_ordering(ordering, classes, mapping):
    classes_num = len(mapping)
    schedule = construct_schedule(ordering, mapping)
    num_by_day = tuple(sum(s is not None for s in day) for day in schedule)

    uniformity = calc_uniformity(num_by_day)

    tightness = 1 - sum(
        sum(class_ is None for class_ in day[first_non_none(day) + 1:first_non_none(reversed(day))])
        if any(class_ is not None for class_ in day) else 0
        for day in schedule
    ) / (PLACES - classes_num)


    suitability = sum(
        
        class_.subject.name in SUITABLE_TIME[week_day][class_num0 + 1]
        for day, week_day in zip(schedule, WeekDay)
        for class_num0, class_ in enumerate(day)
        if class_ is not None
    ) / classes_num
    sleep = sum(day[0] is None for day in schedule) / WORKING_DAYS

    unique_indexes = [
        [[i for i, class_ in enumerate(day) if class_ == unique_class]
         for unique_class in set(day).difference([None])]
        for day in schedule
    ]
    day_grouping = 1 - mean(
        sum(d - 1 for d in diff(class_indexes)) / (day_num - len(class_indexes))
        if len(day) > 1 else 0.
        for day, day_num in zip(unique_indexes, num_by_day) for class_indexes in day
    )

    act_tot_num = [(sum(class_ in day for day in schedule), class_.subject.numbers[class_.type]) for class_ in classes]
    act_min_max = [(act_num, ceil(tot_num / CLASSES_PER_DAY), min(tot_num, WORKING_DAYS))
                   for act_num, tot_num in act_tot_num]
    week_grouping = 1 - mean(
        ((act_num - min_num) / (max_num - min_num))
        if max_num - min_num != 0 else 1.
        for act_num, min_num, max_num in act_min_max
    )

    # noinspection PyRedundantParentheses
    return (C1 * uniformity + C2 * tightness + C3 * suitability + C4 * sleep + C5 * day_grouping + C6 * week_grouping,)


def main(ngen=20, cxpb=0.5, mutpb=0.2):
    lectures = [Class(subject, SubjectType.LECTURE) for subject in SUBJECTS
                for _ in range(subject.numbers[SubjectType.LECTURE])]
    seminars = [Class(subject, SubjectType.SEMINAR) for subject in SUBJECTS
                for _ in range(subject.numbers[SubjectType.SEMINAR])]
    classes = lectures + seminars
    mapping = {i: class_ for i, class_ in enumerate(classes)}

    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    toolbox.register('indices', random.sample, range(PLACES), PLACES)
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.indices)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)

    toolbox.register('evaluate', lambda ordering: eval_ordering(ordering, classes, mapping))
    toolbox.register('mate', tools.cxOrdered)
    toolbox.register('mutate', tools.mutShuffleIndexes, indpb=0.01)
    toolbox.register('select', tools.selTournament, tournsize=3)

    pop = toolbox.population(n=300)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register('avg', np.mean)
    stats.register('std', np.std)
    stats.register('min', np.min)
    stats.register('max', np.max)

    algorithms.eaSimple(pop, toolbox,
        ngen=ngen, cxpb=cxpb, mutpb=mutpb, stats=stats, verbose=True, halloffame=hof)

    timetable_list = []
    for day, day_name in zip(construct_schedule(hof.items[0], mapping), WeekDay):
        print(f'\n{day_name.name}:')
        temp_list = []
        for i, class_ in enumerate(day):
            # print(f'{i + 1})' + (' Free' if class_ is None else f' {class_.subject.name} {class_.type.name}'))
            print(f'{i + 1})' + (' Free' if class_ is None else f' {class_.subject.name}'))
            temp_list.append(' Free' if class_ is None else f' {class_.subject.name}')
        timetable_list.append(temp_list.copy())

    # print(timetable_list)
    return timetable_list


def get_desired_timetable(required_timetables = 3):
    cxpb = 0.1
    mutpb = 0.05

    final_timetables = []

    while True:
        generated_tt = main(cxpb=cxpb, mutpb=mutpb)
        cxpb += 0.1
        mutpb += 0.05

        if cxpb > 1:
            cxpb = 0.1
        if mutpb > 1:
            mutpb = 0.1

        if len(final_timetables) == 0:
            print("Generating 1st TimeTable")
            final_timetables.append(generated_tt)

        else:
            print("Generating ", len(final_timetables)+1, " TimeTable")
            clash = 0
            for i in range(len(final_timetables)):
                clash += compare_timetable(final_timetables[i], generated_tt)

            if (clash != 1):
                final_timetables.append(generated_tt)


        
        if len(final_timetables) >= required_timetables:
            print("Done")
            print( required_timetables , len(final_timetables))
            print("###################\n\n")
            print(final_timetables)
            break

        set_suitable_timing()
    
    return final_timetables



if __name__ == '__main__':

    subject_details = [
        ["S1", "4", "0"],
        ["S2", "4", "0"],
        ["S3", "4", "0"],
        ["S4", "4", "0"],
        ["S5", "4", "0"],
        ["S6", "4", "0"],
        ["S7", "4", "0"],
    ]
    set_subjects(subject_details)
    set_suitable_timing()
    get_desired_timetable(required_timetables=2)
   

    

    



    
