# Uniconnect

 # Timetable Scheduling Using Genetic Algorithm

This project is a Python-based solution for generating optimal weekly timetables using a **genetic algorithm (GA)**. It schedules lectures and labs for a week, ensuring no conflicts, and aims to optimize parameters such as uniformity, suitability, and tightness of schedules.

## Features
- **Genetic Algorithm Optimization**: Utilizes crossover, mutation, and selection to find the best timetable solutions.
- **Custom Subject Input**: You can input the subjects, lectures, and labs to be scheduled.
- **Lab Grouping**: Ensures that labs are grouped into 3 consecutive periods when scheduled.
- **Avoids Conflicts**: Prevents class overlaps and manages subject distribution across the week.
- **Configurable Parameters**: Adjustable parameters like crossover rate (`cxpb`), mutation rate (`mutpb`), and generations (`ngen`) for fine-tuning the GA.



## Getting Started

### Prerequisites
- Python 3.x
- `numpy` and `deap` libraries

# You can install all dependencies by running:
pip install -r requirements.txt
Running the Project
Modify the subject_details in timetable.py with your custom subject names and numbers.
Run the script to generate a timetable:
python timetable.py

The generated timetables will be printed and stored in the output/ folder.

# Example Subject Data
You can configure the subjects and their lectures/labs in the code like this:


subject_details = [
    ["S1", "4", "0"],   # Subject 1 with 4 lectures and 0 labs
    ["S2", "4", "0"],   # Subject 2 with 4 lectures and 0 labs
    ["S3", "4", "3"],   # Subject 3 with 4 lectures and 3 lab sessions
    # Add more subjects as needed
]
Configurable Parameters
You can adjust the following parameters in timetable.py to tune the genetic algorithm:

ngen: Number of generations the algorithm will run.
cxpb: Crossover probability.
mutpb: Mutation probability.
required_timetables: Number of distinct timetables you want to generate.

# Output
The final timetables will be printed to the console and saved in the output/ directory as text files.

# Example Output

MON:
1) S1
2) Free
3) S2
4) S3 (Lab)
5) S3 (Lab)
6) S3 (Lab)
7) Free

...

FRI:
1) S2
2) S1
3) Free
4) S3 (Lab)
5) S3 (Lab)
6) S3 (Lab)
7) Free


# License
This project is licensed under the MIT License - see the LICENSE file for details.
