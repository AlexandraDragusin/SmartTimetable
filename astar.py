import copy
from heapq import heappop, heappush
import time
from check_constraints import parse_interval
import utils

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
        teacher_assignments: dict | None = None,
        teacher_assignments_number: dict | None = None,
        subjects_assignments: dict | None = None,
        conflicts: int | None = None
    ) -> None:

        self.input_data = input_data

        self.schedule = schedule if schedule is not None else\
                        {day: {interval: {classroom: None\
                        for classroom in input_data[CLASSROOMS]}\
                        for interval in input_data[INTERVALS]}\
                        for day in input_data[DAYS]}
        
        self.conflicts_number = conflicts if conflicts is not None\
                                else self.compute_conflicts()

        self.teacher_assignments = teacher_assignments if teacher_assignments is not None\
                                else {teacher : {day : {interval : False\
                                for interval in input_data[INTERVALS]}\
                                for day in input_data[DAYS]} for teacher\
                                 in input_data[TEACHERS].keys()}

        self.teacher_assignments_number = teacher_assignments_number\
                            if teacher_assignments_number is not None\
                            else {teacher : 0  for teacher in input_data[TEACHERS].keys()}
        
        self.subjects_assignments = subjects_assignments if subjects_assignments is not None\
                                    else {subject : 0 for subject in input_data[SUBJECTS]}
   
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
                        interval = str(interval)
                        if interval in teacher_intervals_to_avoid[teacher_name]:
                            constrangeri_incalcate += 1
        
        return constrangeri_incalcate

    def get_next_states(self):
        next_states = []
        schedule = self.schedule

        # Iau toate salile libere si le asignez materii si profesori
        for day in schedule.keys():
            for interval in schedule[day].keys():
                for classroom in schedule[day][interval].keys():
                    if not schedule[day][interval][classroom]:
                        new_states = self.assign_teacher_subject(day, interval, classroom)
                        next_states = list(next_states + new_states)
        return next_states
    
    def assign_teacher_subject(self, day, interval, classroom):
        states = []
        teachers = self.input_data[TEACHERS]
        classrooms = self.input_data[CLASSROOMS]

        # Parcurg materiile neacoperite inca si care se pot preda in classroom
        uncovered_subjects = self.get_uncovered_subjects()
        for subject, _ in uncovered_subjects:
            # Iau profesorii disponibili in acea zi, care nu au deja 7 cursuri planificate si care pot preda materia
            if subject in classrooms[classroom][SUBJECTS]:
                for teacher in teachers.keys():
                    if subject in teachers[teacher][SUBJECTS]\
                        and self.teacher_assignments_number[teacher] < 7\
                        and (not self.teacher_assignments[teacher][day][interval]):
                            
                            # Actualizez orarul
                            new_schedule = copy.deepcopy(self.schedule)
                            new_schedule[day][interval][classroom] = (teacher, subject)

                            # Asigenz profesorul in ziua si intervalul alese
                            new_teacher_assignments = copy.deepcopy(self.teacher_assignments)
                            new_teacher_assignments[teacher][day][interval] = True

                            # Cresc numarul de ore pentru care e asignat profesorul
                            new_teacher_assignments_number = copy.deepcopy(self.teacher_assignments_number)
                            new_teacher_assignments_number[teacher] = self.teacher_assignments_number[teacher] + 1

                            # Actualizez acoperirea materiei
                            new_subjects_assignments = copy.deepcopy(self.subjects_assignments)
                            new_subjects_assignments[subject] = self.subjects_assignments[subject] + classrooms[classroom][CAPACITY]

                            new_state = State(self.input_data, new_schedule, new_teacher_assignments, new_teacher_assignments_number, new_subjects_assignments)
                            
                            states.append(new_state)
                    
        return states

    def compute_conflicts(self):
         # Calculez numarul total de conflcite incalcate
        return check_mandatory_constraints(self.schedule, self.input_data) +  self.check_optional_constraints()

    def is_final(self):
        # Starea finala are 0 conflicte
        return self.conflicts_number == 0

    def clone(self):
        return State(self.input_data, copy.deepcopy(self.schedule), self.conflicts_number, copy.deepcopy(self.teacher_assignments))
    
    def display(self):
        print(self.schedule)

    def get_uncovered_subjects(self):
        # Extrage din lista materiilor, pe cele care nu au fost acoperite in totalitate
        uncovered_subjects = []
        for subject in self.input_data[SUBJECTS]:
            difference = self.input_data[SUBJECTS][subject] - self.subjects_assignments[subject]
            if difference > 0:
                # Salvez numarul de studenti pe care mai trebuie sa ii
                # plasez in clase pt fiecare materie
                uncovered_subjects.append((subject, difference))

        # Sortez descrescator in functie de numarul de studenti ce mai sunt de acoperit
        sorted_uncovered_subjects = sorted(uncovered_subjects, key=lambda x: x[1], reverse=True)

        return sorted_uncovered_subjects

    def get_empty_classrooms(self):
        # Calculeaza numarul de sali goale din orar
        cnt = 0
        for day in self.input_data[DAYS]:
            for interval in self.input_data[INTERVALS]:
                for classroom in self.input_data[CLASSROOMS]:
                    if not self.schedule[day][interval][classroom]:
                        cnt += 1
        return cnt
    
    def __lt__(self, other):
        return self.conflicts_number - other.conflicts_number

    def __hash__(self):
        # Convertesc orarul la un tuplu de tupluri
        schedule_tuples = tuple((day, tuple((interval, tuple(classroom.items())) for interval, classroom in day_schedule.items())) for day, day_schedule in self.schedule.items())
        return hash(schedule_tuples)

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

def heuristic(state):
    return state.conflicts_number +  len(state.get_uncovered_subjects()) * state.get_empty_classrooms()

def astar(start, h, start_time):
    # Lista open in care adaug tupluri (cost_f, nod)
    frontier = []
    heappush(frontier, (0 + h(start), start))

    # Lista closed in care salvez costul pana la nod
    discovered = {start: (0)}
    
    while frontier:
        # Extrag primul nod din frontiera
        node = heappop(frontier)[1]

        # Calculez costul nodului curent
        node_g = discovered[node]

        # Daca este final, opresc cautarea
        if node.is_final():
          break

        next_states = node.get_next_states()
        # Cautam toate starile vecine
        for succ in next_states:
            # Costul catre nodul copil este costul nodului curent + 1
            succ_g = node_g + 1

            # Daca nodul nu a fost descoperit inca sau am gasit un drum cu un cost mai bun
            if succ not in discovered or succ_g < discovered[succ]:
                discovered[succ] = succ_g
                heappush(frontier, (succ_g + h(succ), succ))

        curr_time = time.time()
        if(curr_time - start_time > 240):
            break

    return node, len(discovered.keys())

def start(input_data, input_file):
    initialize_teacher_preferences(input_data)

    start_time = time.time()

    init_state = State(input_data)

    final_state, nr_states = astar(init_state, heuristic, start_time)

    end_time = time.time()

    print("Generated states " + str(nr_states))
    print("Final state conflicts " + str(final_state.conflicts_number))
    print("Execution time for astar:", end_time - start_time, "seconds")
    print("Result shedule:")
    print(utils.pretty_print_timetable_aux_zile(final_state.schedule, input_file))