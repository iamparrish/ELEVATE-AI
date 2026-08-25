"""
Seeds ELEVATE AI with curriculum content and two demo accounts:
  student: aarav.sharma@example.com / password123
  teacher: priya.mehta@example.com  / password123

Demo data for Aarav is produced by actually running quiz/assessment
submissions through the same engine the live app uses, so every metric on
his dashboard is a genuine calculation - not a hand-set number. Run again
any time from a clean DB: `python -m app.database.seed`
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.db import Base, engine, SessionLocal
from app.models.models import (
    User, StudentProfile, TeacherProfile, Subject, Topic, LearningGoal, LearningPreference,
    Question, LearningUnit,
)
from app.utils.security import hash_password
from app.services.quiz_engine import generate_quiz, submit_quiz
from app.services.assessment_engine import build_assessment, submit_assessment
from app.services import learner_model as lm

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ---------------------------------------------------------------- Subjects
SUBJECTS = [
    {"code": "physics", "name": "Physics", "icon": "atom", "description": "Mechanics, energy, electricity and waves."},
    {"code": "mathematics", "name": "Mathematics", "icon": "sigma", "description": "Algebra, equations, trigonometry and probability."},
    {"code": "computer_science", "name": "Computer Science", "icon": "code", "description": "Programming fundamentals and data structures."},
]
subject_objs = {}
for s in SUBJECTS:
    obj = Subject(**s)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    subject_objs[s["code"]] = obj

# ---------------------------------------------------------------- Topics
TOPICS = {
    "physics": [
        ("Motion & Kinematics", "Displacement, velocity, acceleration and equations of motion."),
        ("Work & Energy", "Work done, kinetic and potential energy, conservation of energy."),
        ("Electricity & Circuits", "Current, voltage, resistance and simple circuits."),
        ("Waves & Sound", "Wave properties, frequency, wavelength and sound propagation."),
    ],
    "mathematics": [
        ("Algebra Basics", "Expressions, equations and solving for unknowns."),
        ("Quadratic Equations", "Roots, factoring and the quadratic formula."),
        ("Trigonometry", "Sine, cosine, tangent and right-triangle relationships."),
        ("Probability", "Basic probability, events and combinatorics."),
    ],
    "computer_science": [
        ("Variables & Data Types", "Storing and typing data in a program."),
        ("Loops & Iteration", "For loops, while loops and iteration patterns."),
        ("Functions", "Defining, calling and reasoning about functions."),
        ("Data Structures Basics", "Arrays/lists, stacks and queues."),
    ],
}
topic_objs = {}
for code, topics in TOPICS.items():
    subject = subject_objs[code]
    prev_id = None
    for i, (name, desc) in enumerate(topics):
        t = Topic(subject_id=subject.id, name=name, order_index=i, description=desc,
                   prerequisites=[prev_id] if prev_id else [])
        db.add(t)
        db.commit()
        db.refresh(t)
        topic_objs[name] = t
        prev_id = t.id

# ---------------------------------------------------------------- Goals / Preferences
GOALS = [("exam_prep", "Prepare for exams"), ("concept_mastery", "Build strong concept mastery"),
          ("homework_help", "Get help with homework"), ("curiosity", "Learn out of curiosity")]
for code, label in GOALS:
    db.add(LearningGoal(code=code, label=label))

PREFS = [("visual", "Visual explanations"), ("step_by_step", "Step-by-step guidance"),
         ("practice_heavy", "Practice-heavy learning"), ("concise", "Concise explanations")]
for code, label in PREFS:
    db.add(LearningPreference(code=code, label=label))
db.commit()

# ---------------------------------------------------------------- Question bank
# format: topic_name -> list of (difficulty, type, question, [options], correct_index, explanation, hint)
QUESTION_BANK = {
    "Motion & Kinematics": [
        ("easy", "conceptual", "What quantity describes the rate of change of displacement?",
         ["Velocity", "Force", "Mass", "Energy"], 0,
         "Velocity is defined as the rate of change of displacement with time.",
         "Think about what changes as an object moves over time."),
        ("easy", "conceptual", "Which quantity is a vector: distance or displacement?",
         ["Distance", "Displacement", "Both", "Neither"], 1,
         "Displacement has both magnitude and direction, making it a vector; distance is scalar.",
         "Consider whether direction matters for each quantity."),
        ("medium", "numerical", "A car accelerates uniformly from 0 to 20 m/s in 4 seconds. What is its acceleration?",
         ["3 m/s²", "5 m/s²", "8 m/s²", "10 m/s²"], 1,
         "Acceleration = change in velocity / time = 20/4 = 5 m/s².",
         "Use a = (v - u) / t."),
        ("medium", "application", "A ball is thrown straight up. At the highest point, what is true about its velocity?",
         ["Maximum", "Zero", "Constant", "Negative"], 1,
         "At the highest point, the ball momentarily has zero velocity before falling back down.",
         "Think about the turning point of the motion."),
        ("hard", "numerical", "An object starts at rest and travels 100 m in 5 s under uniform acceleration. Find the acceleration.",
         ["4 m/s²", "8 m/s²", "10 m/s²", "20 m/s²"], 1,
         "Using s = ut + 1/2 at², 100 = 0 + 0.5*a*25, so a = 8 m/s².",
         "Apply the second equation of motion with u = 0."),
    ],
    "Work & Energy": [
        ("easy", "conceptual", "What is the SI unit of work?",
         ["Watt", "Newton", "Joule", "Pascal"], 2,
         "Work is measured in joules (J), the same unit as energy.",
         "Work and energy share the same unit."),
        ("easy", "conceptual", "Kinetic energy depends on an object's mass and its:",
         ["Volume", "Velocity", "Color", "Density"], 1,
         "Kinetic energy = 1/2 m v², so it depends on mass and velocity.",
         "Recall the kinetic energy formula."),
        ("medium", "numerical", "A 2 kg object moves at 3 m/s. What is its kinetic energy?",
         ["3 J", "6 J", "9 J", "18 J"], 2,
         "KE = 1/2 * 2 * 3² = 1/2 * 2 * 9 = 9 J.",
         "Plug values into KE = 1/2 m v²."),
        ("medium", "application", "A book on a shelf has energy due to its height. This is called:",
         ["Kinetic energy", "Potential energy", "Thermal energy", "Sound energy"], 1,
         "Energy due to position/height is gravitational potential energy.",
         "Think about what 'stored due to position' means."),
        ("hard", "scenario", "A pendulum swings from its highest point. As it descends, energy converts mostly from:",
         ["Kinetic to potential", "Potential to kinetic", "Sound to heat", "Kinetic to sound"], 1,
         "As height decreases, potential energy converts into kinetic energy (conservation of energy).",
         "Consider what happens to height and speed together."),
    ],
    "Electricity & Circuits": [
        ("easy", "conceptual", "What quantity is measured in Ohms?",
         ["Current", "Voltage", "Resistance", "Power"], 2,
         "Resistance is measured in Ohms (Ω).",
         "Recall Ohm's law units."),
        ("easy", "conceptual", "In a simple series circuit, current is:",
         ["Different at every point", "The same throughout", "Zero everywhere", "Only at the battery"], 1,
         "In a series circuit, the same current flows through every component.",
         "Think about there being only one path for charge to flow."),
        ("medium", "numerical", "Using V = IR, find the voltage across a 4Ω resistor carrying 2A.",
         ["2V", "4V", "6V", "8V"], 3,
         "V = I * R = 2 * 4 = 8V.",
         "Multiply current by resistance."),
        ("medium", "application", "Adding more resistors in series does what to total resistance?",
         ["Decreases it", "Increases it", "No change", "Makes it zero"], 1,
         "Resistances in series add up, increasing total resistance.",
         "Think about resistors 'in a row'."),
        ("hard", "numerical", "Two resistors of 6Ω and 3Ω are connected in parallel. Find the total resistance.",
         ["1Ω", "2Ω", "4.5Ω", "9Ω"], 1,
         "1/Rt = 1/6 + 1/3 = 1/6 + 2/6 = 3/6, so Rt = 2Ω.",
         "Use the parallel resistance formula."),
    ],
    "Waves & Sound": [
        ("easy", "conceptual", "The distance between two consecutive crests of a wave is called:",
         ["Frequency", "Amplitude", "Wavelength", "Period"], 2,
         "Wavelength is the distance between two consecutive crests (or troughs).",
         "Think about spatial distance, not time."),
        ("easy", "conceptual", "Sound cannot travel through:",
         ["Air", "Water", "Steel", "Vacuum"], 3,
         "Sound needs a medium to travel and cannot pass through a vacuum.",
         "Sound is a mechanical wave requiring particles."),
        ("medium", "numerical", "A wave has frequency 5 Hz and wavelength 2 m. Find its speed.",
         ["2.5 m/s", "7 m/s", "10 m/s", "20 m/s"], 2,
         "Speed = frequency * wavelength = 5 * 2 = 10 m/s.",
         "Use v = f * λ."),
        ("medium", "application", "A higher frequency sound wave is perceived as:",
         ["Louder", "Softer", "Higher pitched", "Lower pitched"], 2,
         "Frequency determines pitch; higher frequency means higher pitch.",
         "Frequency relates to pitch, amplitude relates to loudness."),
        ("hard", "scenario", "As a wave moves from air into water, its speed increases. What generally happens to wavelength if frequency stays constant?",
         ["Increases", "Decreases", "Stays the same", "Becomes zero"], 0,
         "Since v = fλ and frequency is constant, wavelength increases as speed increases.",
         "Rearrange v = f * λ to see what changes with speed."),
    ],
    "Algebra Basics": [
        ("easy", "conceptual", "Solve for x: x + 5 = 12",
         ["5", "6", "7", "17"], 2, "Subtract 5 from both sides: x = 7.", "Isolate x by subtracting 5."),
        ("easy", "conceptual", "Simplify: 3x + 2x",
         ["5x", "6x", "x", "5x²"], 0, "Combine like terms: 3x + 2x = 5x.", "Add the coefficients of x."),
        ("medium", "numerical", "Solve for x: 2x - 4 = 10",
         ["3", "5", "7", "9"], 2, "2x = 14, so x = 7.", "Add 4 to both sides first."),
        ("medium", "application", "If 3 notebooks cost ₹90, what is the cost of 5 notebooks?",
         ["₹120", "₹150", "₹135", "₹100"], 1, "Cost per notebook = 30, so 5 notebooks = 150.", "Find unit cost first."),
        ("hard", "numerical", "Solve: 3(x - 2) = 2(x + 4)",
         ["x = 10", "x = 14", "x = -2", "x = 2"], 1, "3x - 6 = 2x + 8 → x = 14.", "Expand both sides before isolating x."),
    ],
    "Quadratic Equations": [
        ("easy", "conceptual", "The highest power of x in a quadratic equation is:",
         ["1", "2", "3", "0"], 1, "A quadratic equation has degree 2 (highest power is x²).", "Quadratic means 'square'."),
        ("easy", "conceptual", "How many roots does a quadratic equation generally have?",
         ["0", "1", "2", "3"], 2, "A quadratic equation generally has two roots (real or complex).", "Think about the degree of the equation."),
        ("medium", "numerical", "Factorize: x² - 5x + 6 = 0",
         ["x=2,3", "x=1,6", "x=-2,-3", "x=2,-3"], 0, "(x-2)(x-3)=0 gives x=2 or x=3.", "Find two numbers that multiply to 6 and add to -5."),
        ("medium", "application", "For ax² + bx + c = 0, the sum of roots equals:",
         ["-b/a", "c/a", "b/a", "-c/a"], 0, "Sum of roots = -b/a by Vieta's formulas.", "Recall Vieta's formulas."),
        ("hard", "numerical", "Solve using the quadratic formula: x² - 4x - 5 = 0",
         ["x=5,-1", "x=1,-5", "x=5,1", "x=-5,-1"], 0, "x = [4 ± √(16+20)]/2 = [4±6]/2 → x=5 or x=-1.", "Apply x = [-b ± √(b²-4ac)]/2a."),
    ],
    "Trigonometry": [
        ("easy", "conceptual", "In a right triangle, sin(θ) equals:",
         ["Opposite/Hypotenuse", "Adjacent/Hypotenuse", "Opposite/Adjacent", "Hypotenuse/Opposite"], 0,
         "sin(θ) = opposite side / hypotenuse.", "Remember SOH-CAH-TOA."),
        ("easy", "conceptual", "What is cos(0°)?",
         ["0", "0.5", "1", "Undefined"], 2, "cos(0°) = 1.", "Think of the unit circle at angle 0."),
        ("medium", "numerical", "If sin(θ) = 0.6, and it's a right triangle with hypotenuse 10, find the opposite side.",
         ["4", "6", "8", "10"], 1, "Opposite = sin(θ) * hypotenuse = 0.6 * 10 = 6.", "Rearrange sin = opposite/hypotenuse."),
        ("medium", "application", "tan(θ) can be expressed as:",
         ["sin/cos", "cos/sin", "sin*cos", "1/sin"], 0, "tan(θ) = sin(θ)/cos(θ).", "Recall the tangent identity."),
        ("hard", "numerical", "A ladder 10m long leans against a wall making 60° with the ground. How high up the wall does it reach?",
         ["5 m", "8.66 m", "10 m", "6 m"], 1, "Height = 10 * sin(60°) ≈ 10 * 0.866 = 8.66 m.", "Use sin(angle) = opposite/hypotenuse."),
    ],
    "Probability": [
        ("easy", "conceptual", "The probability of an impossible event is:",
         ["1", "0", "0.5", "Undefined"], 1, "An impossible event has probability 0.", "Probability ranges from 0 to 1."),
        ("easy", "conceptual", "What is the probability of getting heads on a fair coin toss?",
         ["0.25", "0.5", "0.75", "1"], 1, "A fair coin has 2 equally likely outcomes, so P(heads) = 1/2.", "Consider equally likely outcomes."),
        ("medium", "numerical", "A die is rolled. What is the probability of getting a number greater than 4?",
         ["1/6", "1/3", "1/2", "2/3"], 1, "Numbers greater than 4 are {5,6}, so P = 2/6 = 1/3.", "List favorable outcomes out of 6."),
        ("medium", "application", "Two coins are tossed. What is the probability of getting exactly one head?",
         ["1/4", "1/2", "3/4", "1"], 1, "Outcomes: HH,HT,TH,TT. Exactly one head: HT,TH → 2/4 = 1/2.", "List all 4 equally likely outcomes."),
        ("hard", "numerical", "A bag has 3 red and 2 blue balls. Find the probability of drawing 2 red balls without replacement.",
         ["3/10", "3/5", "6/20", "1/2"], 0, "P = (3/5)*(2/4) = 6/20 = 3/10.", "Multiply sequential probabilities without replacement."),
    ],
    "Variables & Data Types": [
        ("easy", "conceptual", "Which of these is typically an integer data type value?",
         ["3.14", "\"hello\"", "42", "True/False"], 2, "42 is a whole number, an integer.", "Think about numbers without decimals."),
        ("easy", "conceptual", "What data type would best store a person's name?",
         ["Integer", "Boolean", "String", "Float"], 2, "Text values like names are stored as strings.", "Names are text."),
        ("medium", "application", "What will `x = 5; x = x + 1` result in for x?",
         ["5", "6", "Error", "Undefined"], 1, "x is reassigned to 5+1 = 6.", "Variables can be reassigned to new values."),
        ("medium", "conceptual", "A boolean variable can hold which values?",
         ["Any number", "True or False", "Any text", "Only 0"], 1, "Boolean variables hold True or False.", "Boolean means binary logical value."),
        ("hard", "scenario", "In most languages, dividing an integer by another integer (e.g. 7/2) typically gives:",
         ["3.5 always", "An integer result (3) unless explicitly converted", "An error always", "0"], 1,
         "In many languages integer division truncates, giving 3 unless a float type is used.",
         "Consider how integer division differs from float division."),
    ],
    "Loops & Iteration": [
        ("easy", "conceptual", "A loop that repeats while a condition is true is called a:",
         ["for loop", "while loop", "if statement", "function"], 1, "A while loop repeats as long as its condition remains true.", "Think about condition-based repetition."),
        ("easy", "conceptual", "What does a `for` loop typically iterate over?",
         ["A single value", "A sequence/range", "Nothing", "Only booleans"], 1, "For loops typically iterate over a sequence or range of values.", "Think about repeating for each item."),
        ("medium", "numerical", "How many times does this loop run? `for i in range(5): print(i)`",
         ["4", "5", "6", "Infinite"], 1, "range(5) produces 0,1,2,3,4 - 5 iterations.", "range(n) produces n values starting at 0."),
        ("medium", "application", "What is a risk of writing a `while True` loop without a break condition?",
         ["It runs once", "It never runs", "Infinite loop", "Syntax error"], 2, "Without an exit condition, the loop runs forever - an infinite loop.", "Consider what stops the loop."),
        ("hard", "scenario", "A nested loop (loop inside a loop) running 10 times each takes how many total iterations of the inner loop?",
         ["10", "20", "100", "1"], 2, "10 outer * 10 inner = 100 total inner iterations.", "Multiply outer and inner iteration counts."),
    ],
    "Functions": [
        ("easy", "conceptual", "What is the main purpose of a function in programming?",
         ["To store data", "To reuse a block of logic", "To repeat forever", "To define a variable type"], 1,
         "Functions let you package logic once and reuse it wherever needed.", "Think about avoiding repeated code."),
        ("easy", "conceptual", "What keyword is commonly used to return a value from a function?",
         ["return", "loop", "print", "define"], 0, "The `return` keyword sends a value back from a function.", "Think about how a function 'gives back' a result."),
        ("medium", "application", "If a function has parameters but is called without arguments, what usually happens?",
         ["It always works fine", "An error unless defaults are set", "It returns None always", "It loops forever"], 1,
         "Calling without required arguments raises an error unless default values are defined.", "Consider whether parameters have defaults."),
        ("medium", "conceptual", "What is a 'return value'?",
         ["The function's name", "The output a function produces", "A loop variable", "An error message"], 1,
         "The return value is what a function outputs back to the caller.", "Think of a function as a black box producing output."),
        ("hard", "scenario", "A recursive function that never reaches its base case will most likely cause:",
         ["Faster execution", "A stack overflow / infinite recursion error", "No effect", "A syntax error"], 1,
         "Without a base case, recursive calls never stop, exhausting the call stack.", "Consider what limits recursive calls."),
    ],
    "Data Structures Basics": [
        ("easy", "conceptual", "Which data structure follows First-In-First-Out (FIFO)?",
         ["Stack", "Queue", "Array", "Tree"], 1, "A queue processes elements in the order they arrived: FIFO.", "Think of a real-world queue/line."),
        ("easy", "conceptual", "Which data structure follows Last-In-First-Out (LIFO)?",
         ["Queue", "Array", "Stack", "Graph"], 2, "A stack removes the most recently added element first: LIFO.", "Think of a stack of plates."),
        ("medium", "application", "What is the index of the first element in most array implementations?",
         ["1", "0", "-1", "Depends only on size"], 1, "Most languages use 0-based indexing for arrays.", "Consider zero-based indexing conventions."),
        ("medium", "conceptual", "Which operation adds an element to the end of a list?",
         ["pop", "append", "remove", "sort"], 1, "`append` adds an element to the end of a list.", "Think about which operation 'adds'."),
        ("hard", "scenario", "Removing an element from the middle of an array generally requires:",
         ["No extra work", "Shifting subsequent elements", "Doubling the array size", "Sorting the array first"], 1,
         "Removing a middle element typically shifts later elements to fill the gap.", "Consider how array memory stays contiguous."),
    ],
}

for topic_name, qlist in QUESTION_BANK.items():
    topic = topic_objs[topic_name]
    for difficulty, qtype, text, options, correct_idx, explanation, hint in qlist:
        db.add(Question(
            topic_id=topic.id, subject_id=topic.subject_id, question_text=text, question_type=qtype,
            difficulty=difficulty, options=options, correct_index=correct_idx, explanation=explanation,
            hint=hint, generated_by="bank",
        ))
db.commit()

# ---------------------------------------------------------------- Demo Teacher
teacher = User(full_name="Dr. Priya Mehta", email="priya.mehta@example.com",
               password_hash=hash_password("password123"), role="teacher",
               academic_level="Faculty", institution="Delhi Public School", onboarding_completed=True)
db.add(teacher)
db.commit()
db.refresh(teacher)
db.add(TeacherProfile(user_id=teacher.id, department="Science & Mathematics",
                      subjects_taught=["physics", "mathematics", "computer_science"]))
db.commit()

# ---------------------------------------------------------------- Demo Student: Aarav Sharma
student = User(full_name="Aarav Sharma", email="aarav.sharma@example.com",
               password_hash=hash_password("password123"), role="student",
               academic_level="Grade 10", institution="Delhi Public School", onboarding_completed=True)
db.add(student)
db.commit()
db.refresh(student)

profile = StudentProfile(user_id=student.id, subjects=["physics", "mathematics", "computer_science"],
                          goals=["exam_prep", "concept_mastery"],
                          preferences={"pace": "moderate", "style": "step_by_step"},
                          diagnostic_completed=True)
db.add(profile)
db.commit()

order = 0
for code in profile.subjects:
    subj = subject_objs[code]
    topics = db.query(Topic).filter(Topic.subject_id == subj.id).order_by(Topic.order_index).all()
    for t in topics:
        db.add(LearningUnit(student_id=student.id, topic_id=t.id, order_index=order))
        order += 1
db.commit()

# Generate REAL learning events by actually running quizzes/assessments through
# the same engine the live app uses. This produces genuinely different,
# earned mastery per topic instead of hand-set numbers.
import random
random.seed(42)


def run_quiz(topic_name, difficulty, n, correct_ratio):
    topic = topic_objs[topic_name]
    quiz, questions = generate_quiz(db, student.id, "custom", topic_id=topic.id, difficulty=difficulty, num_questions=n)
    if not questions:
        return
    answers = []
    for i, q in enumerate(questions):
        correct = random.random() < correct_ratio
        selected = q.correct_index if correct else (q.correct_index + 1) % len(q.options)
        answers.append({"question_id": q.id, "selected_index": selected, "response_time_seconds": random.randint(10, 45)})
    submit_quiz(db, quiz, student.id, answers, time_taken_seconds=n * 25)


# Strong topic: Motion & Kinematics - mastered through consistent good performance
run_quiz("Motion & Kinematics", "easy", 3, 0.9)
run_quiz("Motion & Kinematics", "medium", 3, 0.85)
run_quiz("Motion & Kinematics", "hard", 2, 0.8)

# Developing topic: Algebra Basics - mixed but improving
run_quiz("Algebra Basics", "easy", 3, 0.6)
run_quiz("Algebra Basics", "medium", 3, 0.75)

# Weak topic / knowledge gap: Electricity & Circuits - repeated poor performance
run_quiz("Electricity & Circuits", "easy", 3, 0.4)
run_quiz("Electricity & Circuits", "medium", 3, 0.25)
run_quiz("Electricity & Circuits", "medium", 2, 0.3)

# In progress: Variables & Data Types - just getting started
run_quiz("Variables & Data Types", "easy", 3, 0.66)

# One diagnostic-style assessment across a couple of subjects (not inflating scores)
assessment = build_assessment(db, student.id, "recommended", subject_id=subject_objs["mathematics"].id, num_questions=6)
if assessment.question_ids:
    from app.models.models import Question as Q
    answers = []
    for qid in assessment.question_ids:
        q = db.query(Q).filter(Q.id == qid).first()
        correct = random.random() < 0.7
        selected = q.correct_index if correct else (q.correct_index + 1) % len(q.options)
        answers.append({"question_id": qid, "selected_index": selected, "topic_id": q.topic_id})
    submit_assessment(db, assessment, student.id, answers)

# A little material engagement + tutor usage so those code paths have real data too.
lm.log_event(db, student.id, "material_opened", topic_id=topic_objs["Work & Energy"].id, duration_seconds=120)
lm.log_event(db, student.id, "tutor_session", topic_id=topic_objs["Motion & Kinematics"].id, duration_seconds=90)

lm.recalc_recommendations(db, student.id)
lm.notify(db, student.id, "reminder", "Welcome to ELEVATE AI",
          "Your personalized learning path is ready. Start with your recommended practice today.")

db.close()

print("Seed complete.")
print("Student login: aarav.sharma@example.com / password123")
print("Teacher login: priya.mehta@example.com / password123")
