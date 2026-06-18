import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

# ==========================================
# 1. LOAD & CLEAN DATASET (ML STAGE)
# ==========================================
print("🔄 Loading dataset and training ML model...")
df = pd.read_csv('cleaned_dataset.csv')

# Drop non-predictive features (Text/IDs) as planned in your pipeline
X = df.drop(columns=['Number', 'Time Taken (days)', 'User'])

# Ensure target variable y is strictly treated as float numeric values
y = df['Time Taken (days)'].astype(float)

# Split into 80% train and 20% test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the best-performing model mentioned in the README
ml_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
ml_model.fit(X_train, y_train)

# Evaluate it safely 
y_pred = ml_model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"✅ ML Model Trained! Baseline Mean Absolute Error: {mae:.2f} days\n")


# ==========================================
# 2. DEFINE RESOURCES, SKILLS & DEPENDENCIES
# ==========================================
developers = {
    0: {"name": "Junior Developer", "cost_per_day": 150, "max_days_limit": 5, "max_difficulty": 1},
    1: {"name": "Mid-Level Developer", "cost_per_day": 300, "max_days_limit": 5, "max_difficulty": 2},
    2: {"name": "Senior Developer", "cost_per_day": 600, "max_days_limit": 5, "max_difficulty": 3}
}

new_tasks_pool = X_test.head(8).copy()
num_tasks = len(new_tasks_pool)
num_devs = len(developers)

# Pre-compute durations upfront to make your loop lightning fast 🏎️
predicted_durations = ml_model.predict(new_tasks_pool)

# Add mock task difficulties (1=Easy, 2=Med, 3=Hard)
np.random.seed(10) 
task_difficulties = np.random.choice([1, 2, 3], size=num_tasks, p=[0.4, 0.4, 0.2])

# Define the task dependency mapping 🔗
task_dependencies = {
    2: [0],
    5: [1, 2],
    7: [4]
}


# ==========================================
# 3. GENETIC ALGORITHM LOGIC (OPTIMIZER STAGE)
# ==========================================

# A. Fitness Function (Evaluates how good or bad a schedule is)
def evaluate_schedule(chromosome):
    dev_workload_days = {i: 0 for i in range(num_devs)}
    task_end_times = {} 
    total_cost = 0
    penalty = 0
    
    for task_idx, dev_id in enumerate(chromosome):
        predicted_days = predicted_durations[task_idx]
        task_difficulty = task_difficulties[task_idx]
        dev_profile = developers[dev_id]
        
        # Skill constraint check
        if task_difficulty > dev_profile["max_difficulty"]:
            penalty += 15000 
            
        # Dependency timeline checker
        dependency_ready_time = 0
        if task_idx in task_dependencies:
            for dep_task in task_dependencies[task_idx]:
                dep_finish_time = task_end_times.get(dep_task, 0)
                dependency_ready_time = max(dependency_ready_time, dep_finish_time)
        
        # Timeline logic
        start_time = max(dev_workload_days[dev_id], dependency_ready_time)
        end_time = start_time + predicted_days
        
        task_end_times[task_idx] = end_time
        dev_workload_days[dev_id] = end_time 
        total_cost += predicted_days * dev_profile["cost_per_day"]
        
    total_sprint_duration = max(task_end_times.values()) if task_end_times else 0
    
    # Overload capacity check
    for dev_id, total_days in dev_workload_days.items():
        if total_days > developers[dev_id]["max_days_limit"]:
            overshoot = total_days - developers[dev_id]["max_days_limit"]
            penalty += overshoot * 10000  
            
    penalty += total_sprint_duration * 500
            
    return total_cost + penalty, dev_workload_days, total_cost, total_sprint_duration

# B. Custom Genetic Algorithm Operators
def create_individual():
    return list(np.random.randint(0, num_devs, size=num_tasks))

def crossover(parent1, parent2):
    point = np.random.randint(1, num_tasks - 1)
    return parent1[:point] + parent2[point:], parent2[:point] + parent1[point:]

def mutate(individual, probability=0.2):
    for i in range(len(individual)):
        if np.random.rand() < probability:
            individual[i] = np.random.randint(0, num_devs)
    return individual

# C. Running the Evolution Loop
POPULATION_SIZE = 50
GENERATIONS = 40

# Initialize random schedules
population = [create_individual() for _ in range(POPULATION_SIZE)]

print("🧬 Evolutionary Optimizer running with Dependencies...")
for generation in range(GENERATIONS):
    # Score the population
    scored_pop = []
    for ind in population:
        score, _, _, _ = evaluate_schedule(ind)
        scored_pop.append((score, ind))
        
    # Sort from cheapest/best to worst
    scored_pop.sort(key=lambda x: x[0])
    
    # 🛡️ TRUE ELITISM: Save the absolute best individual perfectly
    next_generation = [scored_pop[0][1]]
    
    # Create the breeding pool from the top 20
    breeding_pool = [ind for score, ind in scored_pop[:20]]
    
    # Crossover and Mutate to fill the rest of the pool
    while len(next_generation) < POPULATION_SIZE:
        p1 = breeding_pool[np.random.randint(0, len(breeding_pool))]
        p2 = breeding_pool[np.random.randint(0, len(breeding_pool))]
        
        c1, c2 = crossover(p1, p2)
        next_generation.append(mutate(c1))
        if len(next_generation) < POPULATION_SIZE:
            next_generation.append(mutate(c2))
            
    population = next_generation

# ==========================================
# 4. PRINT THE OPTIMAL SCHEDULE RESULTS
# ==========================================
best_schedule = population[0]
final_score, final_workload, final_cost, final_duration = evaluate_schedule(best_schedule)

print("\n🏆 OPTIMIZATION COMPLETE! Best Found Task Schedule:")
print("-" * 50)
for task_idx, dev_id in enumerate(best_schedule):
    print(f"Task #{task_idx+1} ──► Assigned to: {developers[dev_id]['name']}")

print("-" * 50)
print("📊 FINAL TEAM WORKLOAD SUMMARY:")
for dev_id, days in final_workload.items():
    status = "⚠️ OVERLOADED" if days > developers[dev_id]['max_days_limit'] else "✅ SAFE"
    print(f" • {developers[dev_id]['name']}: Total Predicted Work = {days:.2f} Days ({status})")

print(f"\n💵 Optimized Operational Financial Cost: ${final_cost:.2f}")