from dwave.system import LeapHybridSampler
from dimod import BinaryQuadraticModel
from collections import defaultdict
import matplotlib.pyplot as plt

# Define the number of scrutinizers and bills
n_scrutinizerJunior = 2
n_scrutinizerIntermediate = 2
n_scrutinizerSenior = 1
n_Scrutinizers = n_scrutinizerJunior + n_scrutinizerIntermediate + n_scrutinizerSenior

n_billEasy = 2
n_billMedium = 3
n_billHard = 1
nBills = n_billEasy + n_billMedium + n_billHard

# Define the time limit for bills to be reviewed
time_limit = 10

# Initialize QUBO matrix
Q = defaultdict(int)

# Define constants for rewards and penalties
reward = -1  # Reward for a valid assignment
penalty = 10  # Penalty for an invalid assignment
time_penalty = 1  # Penalty for exceeding the time limit

# Define assignment variables
variables = [(i, j) for i in range(n_Scrutinizers) for j in range(nBills)]

# Function to get index of the QUBO matrix for a given variable
def get_index(i, j):
    return i * nBills + j

# Populate the QUBO matrix with rewards, penalties, and time constraints
for i, j in variables:
    index = get_index(i, j)
    # Determine the scrutinizer's level and the bill's difficulty
    level = 'Senior' if i < n_scrutinizerSenior else ('Intermediate' if i < n_scrutinizerSenior + n_scrutinizerIntermediate else 'Junior')
    difficulty = 'Hard' if j < n_billHard else ('Medium' if j < n_billHard + n_billMedium else 'Easy')

    # Assign rewards and penalties based on the level and difficulty
    if (level == 'Senior') or (level == 'Intermediate' and difficulty != 'Hard') or (level == 'Junior' and difficulty == 'Easy'):
        Q[(index, index)] = reward
    else:
        Q[(index, index)] = penalty

    # Time penalties (simplified)
    # For simplicity, assume each scrutinizer works in sequential order and each bill takes a day
    if level == 'Junior':
        capacity = 1  # Junior can check only easy bills
    elif level == 'Intermediate':
        capacity = 2  # Intermediate can check easy and medium bills
    elif level == 'Senior':
        capacity = 3  # Senior can check all bills

    for k in range(capacity, nBills):
        # Only for bills that are beyond the scrutinizer's capacity
        Q[(index, get_index(i, k))] += time_penalty

# Ensure each bill is assigned to only one scrutinizer
for j in range(nBills):
    for i in range(n_Scrutinizers):
        for k in range(i+1, n_Scrutinizers):
            Q[(get_index(i, j), get_index(k, j))] += penalty

# Create the QUBO model
bqm = BinaryQuadraticModel.from_qubo(Q)

# Solve the problem using a hybrid sampler
sampler = LeapHybridSampler()
results = sampler.sample(bqm, label='Example - Scrutinizer Assignment')

# Process the results
sampleset = results.first.sample
energy = results.first.energy
print("Sample:", sampleset)
print("Energy:", energy)

# Function to convert sample to scrutinizer-bill assignments including time
def sample_to_assignments_with_time(sample, n_Scrutinizers, nBills, time_limit):
    assignments = defaultdict(list)  # Change to a dictionary mapping bills to a list of scrutinizers
    for index, value in sample.items():
        if value and index < n_Scrutinizers * nBills:
            scrutinizer, bill = divmod(index, nBills)
            assignments[scrutinizer].append(bill)  # Assign the bill to one scrutinizer
    return assignments

# Convert sample to assignments including time
assignments_with_time = sample_to_assignments_with_time(sampleset, n_Scrutinizers, nBills, time_limit)

# Define scrutinizer_labels with levels
scrutinizer_labels_with_levels = []
for i in range(n_Scrutinizers):
    level = 'Senior' if i < n_scrutinizerSenior else ('Intermediate' if i < n_scrutinizerSenior + n_scrutinizerIntermediate else 'Junior')
    scrutinizer_labels_with_levels.append(f"Scrutinizer {i+1} ({level})")

# Visualization for assignments
plt.figure(figsize=(12, 6))

# First subplot for Scrutinizer-Bill Assignments
plt.subplot(1, 2, 1)
for scrutinizer, bills in assignments_with_time.items():
    for bill in bills:
        # Determine the correct x-position based on bill type
        if bill < n_billEasy:
            bill_type = 'Easy'
            bill_x_position = bill  # Easy bill index
        elif bill < n_billEasy + n_billMedium:
            bill_type = 'Medium'
            bill_x_position = bill - n_billEasy  # Medium bill index after adjusting for easy bills
        else:
            bill_type = 'Hard'
            bill_x_position = bill - (n_billEasy + n_billMedium)  # Hard bill index after adjusting for easy and medium bills
        plt.plot(bill_x_position, scrutinizer, 'bo')

# Generate bill labels dynamically based on the number of each type
bill_labels = ['Easy'] * n_billEasy + ['Medium'] * n_billMedium + ['Hard'] * n_billHard

# Set up the plot
plt.xlabel('Bills')
plt.ylabel('Scrutinizers')
plt.xticks(range(nBills), bill_labels, rotation=45)
plt.yticks(range(n_Scrutinizers), scrutinizer_labels_with_levels)
plt.title('Scrutinizer-Bill Assignments')
plt.grid(True)

# Second subplot for Bills per Scrutinizer
plt.subplot(1, 2, 2)

# Initialize bill count with zeros
bill_count = [0] * n_Scrutinizers

# Fill in the bill_count with the number of bills for each scrutinizer
for scrutinizer, bills in assignments_with_time.items():
    bill_count[scrutinizer] = len(bills)

# Plotting the bar chart
plt.bar(scrutinizer_labels_with_levels, bill_count)
plt.xlabel('Scrutinizers')
plt.ylabel('Number of Bills Assigned')
plt.title('Bills per Scrutinizer')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig("scrutinizer_bill_assignments.png", format='png')
plt.show()
