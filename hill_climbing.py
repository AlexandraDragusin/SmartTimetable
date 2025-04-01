import copy
import random
import time
import utils
from check_constraints import parse_interval
import matplotlib.pyplot as plt

MAX_NUMBER_GENERATED_STATES = 10
MAX_CLASSROOM_TO_MOVE = 60

INTERVALS = 'Intervale'
DAYS = 'Zile'
SUBJECTS = 'Materii'
TEACHERS = 'Profesori'
CLASSROOMS = 'Sali'
CAPACITY = 'Capacitate'

teacher_preferences = {}
teacher_intervals_to_avoid = {}

class State:
    def __init__(
        self,
        input_data,
        schedule: dict | None = None,
        conflicts: int | None = None,
        teacher_assignments: dict | None = None
    ) -> None:

        self.input_data = input_data

        self.schedule = schedule if schedule is not None else\
                        self.generate_schedule(self.input_data[INTERVALS],
                        self.input_data[SUBJECTS], self.input_data[TEACHERS],
                        self.input_data[CLASSROOMS], self.input_data[DAYS])
        
        self.conflicts_number = conflicts if conflicts is not None else self.compute_conflicts()

        self.teacher_assignments = teacher_assignments if teacher_assignments\
                                 is not None else self.compute_teacher_assignments()

    def generate_schedule(self, intervals, subjects, teachers, classrooms, days):
        # Generarea unui orar care satisface toate constrangerile obligatoriii
        tries = 50
        while tries > 0:
            schedule = {day: {interval: {classroom: None for classroom in classrooms} for interval in intervals} for day in days}

            available_classrooms = {day: {interval: {subject: [classroom for classroom in classrooms if subject in classrooms[classroom][SUBJECTS]] for subject in subjects} for interval in intervals} for day in days}
            
            subjects_capacity = {subject : 0 for subject in subjects}

            teacher_total_assignments = {teacher : 0  for teacher in teachers.keys()}

            teacher_assignments = {teacher : {day : {interval : False for interval in intervals} for day in days} for teacher in teachers.keys()}

            subjects_list = list(subjects.keys())
            number_of_subjects_chosen = 0

            # Ma opresc atunci cand am alocat toate materiile in sali
            while number_of_subjects_chosen < len(subjects):
                subject = random.choice(subjects_list)
                number_of_subjects_chosen += 1

                subject_assigned = False
                attempts = 0

                # Cat timp nu am terminat de alocat toti studentii acestei materii
                while not subject_assigned:
                    # Aleg o zi si un interval random
                    day = random.choice(days)
                    interval = random.choice(intervals)

                    # Aleg random o sala din salile disponibile in ziua si intervalul alese
                    available = available_classrooms[day][interval][subject]
                    if not available:
                        attempts += 1
                        if attempts >= 20:
                            break
                        continue
                    classroom = random.choice(available)

                    # Selectez profesorii care pot preda materia aleasa si care nu au deja
                    # un curs asignat in ziua si intervalul alese
                    valid_teachers = []
                    for teacher in teachers.keys():
                        if subject in teachers[teacher][SUBJECTS]\
                            and teacher_total_assignments[teacher] < 7\
                            and (not teacher_assignments[teacher][day][interval]):
                    
                            valid_teachers.append(teacher)

                    if not valid_teachers:
                        attempts += 1
                        if attempts >= 20:
                            break
                        continue

                    # Aleg random un profesor si il asigenz in ziua, intervalul, clasa alese
                    teacher = random.choice(valid_teachers)
                    teacher_total_assignments[teacher] += 1
                    teacher_assignments[teacher][day][interval] = True

                    schedule[day][interval][classroom] = (teacher, subject)

                    # Sterg clasa aleasa din listele tututror materiilor care pot fi tinute in acea sala
                    for subj in subjects:
                        available_classrooms[day][interval][subj] = [c for c in available_classrooms[day][interval][subj] if c != classroom]

                    # Actualizez acoperirea materiei
                    subjects_capacity[subject] += classrooms[classroom]['Capacitate']

                    # Am atins capacitatea dorita
                    if subjects_capacity[subject] >= subjects[subject]:
                        subject_assigned = True
                        # Sterg materia din lista de materii
                        subjects_list.remove(subject)
            
            # Ma opresc din cautare atunci cand orarul generat are indeplinite
            # toate constrangerile obligatorii
            if check_mandatory_constraints(schedule, self.input_data) == 0:
                break            
            tries -= 1

        self.teacher_assignments = teacher_assignments
        
        return schedule
   
    def check_optional_constraints(self):
        # Calculeaza numerul constrangerilor optionale
        constrangeri_incalcate = 0

        for day, intervals in self.schedule.items():
            for interval, classrooms in intervals.items():
                for _, assignment in classrooms.items():
                    if assignment:
                        teacher_name = assignment[0]

                        # Profesorul nu prefera sa predea in aceasta zi
                        if not teacher_preferences[teacher_name].get(day, True):
                            constrangeri_incalcate += 1 

                        # Profesorul nu doreste sa predea in acest interval
                        if str(interval) in teacher_intervals_to_avoid[teacher_name]:
                            constrangeri_incalcate += 1

        return constrangeri_incalcate

    def get_next_states(self):
        # Generez stari vecine pentru starea curenta
        next_states = []
        schedule = self.schedule
        
        # Ma opresc cand am gasim MAX_NUMBER_GENERATED_STATES de stari vecine diferite
        # sau cand am incercat sa fac mutari pentru MAX_CLASSROOM_TO_MOVE clase
        iters = 0
        while len(next_states) < MAX_NUMBER_GENERATED_STATES and iters < MAX_CLASSROOM_TO_MOVE:
            # Aleg random o zi, un interval, o clasa
            day = random.choice(list(schedule.keys()))
            interval = random.choice(list(schedule[day].keys()))
            classroom = random.choice(list(schedule[day][interval].keys()))

            # Realizez mutari ale clasei daca aceasta exista in orar
            if schedule[day][interval][classroom]:
                iters += 1
                new_states = self.apply_move(day, interval, classroom)
                next_states = list(set(next_states + new_states))

        return next_states
    
    def apply_move(self, prev_day, prev_interval, prev_classroom):
        states = []
        schedule = self.schedule
        prev_teacher, subject = schedule[prev_day][prev_interval][prev_classroom]

        # Caut noi zile, intervale, clase pentru care se satisfac urmatoarele conditii:
        # - profesorul materiei poate preda in ziua si intervalul nou
        # - materia poate fi predata in clasa noua
        # - clasele interschimbate au aceeasi capacitate 

        for day in self.input_data[DAYS]:
            for interval in self.input_data[INTERVALS]:
                if not self.teacher_assignments[prev_teacher][day][interval]:
                    for classroom in self.input_data[CLASSROOMS]:
                        if (subject in self.input_data[CLASSROOMS][classroom][SUBJECTS]) and \
                            self.input_data[CLASSROOMS][classroom]['Capacitate'] == self.input_data[CLASSROOMS][prev_classroom]['Capacitate']\
                            and (day != prev_day or interval != prev_interval or classroom != prev_classroom):
                            
                            new_schedule = copy.deepcopy(schedule)

                            # Caclulez conflictele soft generate de asezarea profesorului in
                            # ziua, intervalul si sala curenta 
                            prev_constraints = 0
                            if prev_interval in teacher_intervals_to_avoid[prev_teacher]:
                                prev_constraints += 1
                            if not teacher_preferences[prev_teacher][prev_day]:
                                prev_constraints += 1

                            # Calculez conflictele soft pe care le-ar genera mutarea
                            # profesorului in ziua, intervalul si sala noua
                            next_constraints = 0
                            if interval in teacher_intervals_to_avoid[prev_teacher]:
                                next_constraints += 1
                            if not teacher_preferences[prev_teacher][day]:
                                next_constraints += 1

                            # Sala in care vreau sa ma mut nu este ocupata
                            if schedule[day][interval][classroom] == None:
                                # Realizez mutarea doar daca ma avantajeaza noua structura
                                if prev_constraints > next_constraints:
                                    # Eliberez sala in ziua si intervalul precedent
                                    new_schedule[prev_day][prev_interval][prev_classroom] = None
                                    new_schedule[day][interval][classroom] = (prev_teacher, subject)
                                    
                                    # Calculez noul numar de conflicte
                                    new_confl = self.conflicts_number - (prev_constraints - next_constraints)

                                    # Asignez profesorul in ziua, intervalul si sala noua
                                    new_teach_assignm = copy.deepcopy(self.teacher_assignments)
                                    new_teach_assignm[prev_teacher][prev_day][prev_interval] = False
                                    new_teach_assignm[prev_teacher][day][interval] = True

                                    states.append(State(self.input_data, new_schedule, new_confl, new_teach_assignm))

                            # Sala este ocupata
                            else:
                                new_teacher, _ = schedule[day][interval][classroom]

                                # Fac interschimbarea claselor daca profesorul nou nu preda in ziua si
                                #  intervalul in care vreau sa il mut
                                if not self.teacher_assignments[new_teacher][prev_day][prev_interval] and\
                                    schedule[day][interval][classroom][1] in self.input_data[CLASSROOMS][prev_classroom][SUBJECTS]:

                                    # Caclulez conflictele soft generate de asezarea profesorului cu care
                                    #  fac schimbul in ziua, intervalul si sala in care tine cursul
                                    if interval in teacher_intervals_to_avoid[new_teacher]:
                                        prev_constraints += 1
                                    if not teacher_preferences[new_teacher][day]:
                                        prev_constraints += 1
                                    
                                    # Caclulez conflictele soft generate de asezarea profesorului cu care
                                    # fac schimbul in ziua, intervalul si sala in care vreau sa il mut
                                    if prev_interval in teacher_intervals_to_avoid[new_teacher]:
                                        next_constraints += 1
                                    if not teacher_preferences[new_teacher][prev_day]:
                                        next_constraints += 1

                                    # Daca noua structura a orarului produce mai putine conflicte, aleg sa
                                    # fac inetrschimbarea
                                    if prev_constraints > next_constraints:
                                        new_schedule[prev_day][prev_interval][prev_classroom] = schedule[day][interval][classroom]
                                        new_schedule[day][interval][classroom] = (prev_teacher, subject)

                                        # Calculez noul numar de conflicte
                                        new_confl = self.conflicts_number - (prev_constraints - next_constraints)

                                        # Asignez profesorul in ziua, intervalul si sala noua in care va preda
                                        new_teach_assignm = copy.deepcopy(self.teacher_assignments)
                                        new_teach_assignm[prev_teacher][prev_day][prev_interval] = False
                                        new_teach_assignm[prev_teacher][day][interval] = True
                                        new_teach_assignm[new_teacher][day][interval] = False
                                        new_teach_assignm[new_teacher][prev_day][prev_interval] = True

                                        states.append(State(self.input_data, new_schedule, new_confl, new_teach_assignm))

        return states

    def compute_conflicts(self):
        # Calculez numarul total de conflcite incalcate
        return check_mandatory_constraints(self.schedule, self.input_data) +  self.check_optional_constraints()

    def compute_teacher_assignments(self):
        # Parcurg orarul si marchez zilele si intervalele in care un profesor preda
        teacher_assignments = {teacher : {day : {interval : False for interval in self.input_data[INTERVALS]} for day in self.input_data[DAYS]} for teacher in self.input_data[TEACHERS].keys()}

        for day, intervals in self.schedule.items():
            for interval, classrooms in intervals.items():
                for _, assignment in classrooms.items():
                    if assignment:
                        teacher_name = assignment[0]
                        teacher_assignments[teacher_name][day][interval] = True
        
        return teacher_assignments

    def is_final(self):
        # Starea finala are 0 conflicte
        return self.conflicts_number == 0

    def clone(self):
        return State(self.input_data, copy.deepcopy(self.schedule), self.conflicts_number, copy.deepcopy(self.teacher_assignments))
    
    def display(self):
        print(self.schedule)

def check_mandatory_constraints(timetable, timetable_specs):
        # Functie de verificare a constrangerilor obligatorii din utils.py, din care am sters mesajele printate
        constrangeri_incalcate = 0

        acoperire_target = timetable_specs[SUBJECTS]
        
        acoperire_reala = {subject : 0 for subject in acoperire_target}

        ore_profesori = {prof : 0 for prof in timetable_specs[TEACHERS]}

        for day in timetable:
            for interval in timetable[day]:
                profs_in_crt_interval = []
                for room in timetable[day][interval]:
                    if timetable[day][interval][room]:
                        prof, subject = timetable[day][interval][room]
                        acoperire_reala[subject] += timetable_specs[CLASSROOMS][room]['Capacitate']

                        # PROFESORUL PREDĂ 2 MATERII ÎN ACELAȘI INTERVAL
                        if prof in profs_in_crt_interval:
                            constrangeri_incalcate += 1
                        else:
                            profs_in_crt_interval.append(prof)

                        # MATERIA NU SE PREDA IN SALA
                        if subject not in timetable_specs[CLASSROOMS][room][SUBJECTS]:
                            constrangeri_incalcate += 1

                        # PROFESORUL NU PREDA MATERIA
                        if subject not in timetable_specs[TEACHERS][prof][SUBJECTS]:
                            constrangeri_incalcate += 1

                        ore_profesori[prof] += 1

        # CONDITIA DE ACOPERIRE
        for subject in acoperire_target:
            if acoperire_reala[subject] < acoperire_target[subject]:
                constrangeri_incalcate += 1

        # CONDITIA DE MAXIM 7 ORE PE SĂPTĂMÂNĂ
        for prof in ore_profesori:
            if ore_profesori[prof] > 7:
                constrangeri_incalcate += 1

        return constrangeri_incalcate

def hill_climbing(initial: State, max_iters: int = 1000):
    iters, states = 0, 0
    state = initial.clone()
    
    while iters < max_iters:
        iters += 1

        # Return daca starea curenta este cea finala 
        if state.is_final():
            return state.is_final(), iters, states, state
        
        # Construiesc starile vecine ale starii curente
        next_states = list(state.get_next_states())

        # Adun la numarul total de stari construite
        states += len(next_states)
        
        # Daca nu gasesc stari vecine, ma opresc
        if len(next_states) == 0:
            return state.is_final(), iters, states, state

        # Salvez starea vecina cu cele mai putine conflicte
        minState = next_states[0]
        minConflicts = minState.conflicts_number

        for succ in next_states:
            if succ.conflicts_number < minConflicts:
                minState = succ
                minConflicts = succ.conflicts_number

        # Nu am gasit o stare vecina mai buna
        if minConflicts >= state.conflicts_number:
            return state.is_final(), iters, states, state
        
        state = minState
        
    return state.is_final(), iters, states, state

def random_restart_hill_climbing(
    initial: State,
    max_restarts: int = 100, 
    run_max_iters: int = 100):

    is_final = False
    total_iters, total_states = 0, 0
    
    # Realizez max_restarts căutări de tip Hill Climbing, din stări initiale create random
    best_state = initial

    restarts = 0
    state = initial

    while restarts < max_restarts:
        restarts += 1

        init_state_conflicts = state.conflicts_number

        is_final, iters, states, state = hill_climbing(state, run_max_iters)

        if state.conflicts_number < best_state.conflicts_number:
            best_state = state

        # Adun numarul de iteratii si stari create de alg hill_climbing
        total_iters += iters
        total_states += states

        # Daca am ajuns intr-o stare finala, ma opresc
        if is_final:
            return is_final, total_iters, total_states, state, init_state_conflicts

        state = State(state.input_data)
    
    # Am epuizat numarul de restart-rui, intorc cea mai buna stare gasita
    return is_final, total_iters, total_states, best_state, init_state_conflicts

def initialize_teacher_preferences(input_data):
    global teacher_preferences
    global teacher_intervals_to_avoid
    
    # Parcurg preferintele fiecarui profesor
    for teacher, details in input_data[TEACHERS].items():
        teacher_preferences[teacher] = {}
        teacher_intervals_to_avoid[teacher] = []
        for const in details['Constrangeri']:
            if const[0] != '!':
                # Salvez zilele in care prefera sa predea
                if const in input_data[DAYS]:
                    teacher_preferences[teacher][const] = True
            else:
                const = const[1:]
                # Salvez zilele in care prefera sa nu predea
                if const in input_data[DAYS]:
                    day = const
                    teacher_preferences[teacher][day] = False
                elif '-' in const:
                    # Fac o lista cu intervalele in care prefera sa nu predea
                    interval = parse_interval(const)
                    if interval[0] != interval[1] - 2:
                        intervals = [(i, i + 2) for i in range(interval[0], interval[1], 2)]
                        for interval in intervals:
                            teacher_intervals_to_avoid[teacher].append(str(interval))
                    else:
                        teacher_intervals_to_avoid[teacher].append(str(interval))

def start(input_data, input_file):
    # Initializez preferintele profesorilor in functie de datele de intrare
    initialize_teacher_preferences(input_data)

    # Setez seed random
    random.seed(random.random())

    start_time = time.time()
    # Creez starea initiala
    init_state = State(input_data)

    # Rulez algoritmul
    is_final, iter_num, num_states, final_state, init_state_conflicts = random_restart_hill_climbing(init_state, 50, 100)
    end_time = time.time()

    print("Initial state conflicts number: ", init_state_conflicts)
    print("Execution time for hc:", end_time - start_time, "seconds")
    print("Generated states " + str(num_states))
    print("Final state conflicts " + str(final_state.conflicts_number))
    print("Total iters ", iter_num)
    print("Result shedule:")
    print(utils.pretty_print_timetable_aux_zile(final_state.schedule, input_file))
