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
# 2. DEFINE DEVELOPER RESOURCES & NEW TASKS
# ==========================================
# Mock team setup for the Genetic Algorithm Optimizer
developers = {
    0: {"name": "Junior Developer", "cost_per_day": 150, "max_days_limit": 5},
    1: {"name": "Mid-Level Developer", "cost_per_day": 300, "max_days_limit": 5},
    2: {"name": "Senior Developer", "cost_per_day": 600, "max_days_limit": 5}
}

# Grab 8 new unassigned tasks from your test data to simulate a sprint planning session
new_tasks_pool = X_test.head(8)
num_tasks = len(new_tasks_pool)
num_devs = len(developers)


# ==========================================
# 3. GENETIC ALGORITHM LOGIC (OPTIMIZER STAGE)
# ==========================================

# A. Fitness Function (Evaluates how good or bad a schedule is)
def evaluate_schedule(chromosome):
    dev_workload_days = {i: 0 for i in range(num_devs)}
    total_cost = 0
    
    # Calculate days and cost based on ML predictions
    for task_idx, dev_id in enumerate(chromosome):
        task_features = new_tasks_pool.iloc[[task_idx]]
        predicted_days = float(ml_model.predict(task_features)[0])
        
        dev_workload_days[dev_id] += predicted_days
        total_cost += predicted_days * developers[dev_id]["cost_per_day"]
        
    # Penalty System: Add huge cost if a developer breaks their safe workload threshold
    penalty = 0
    for dev_id, total_days in dev_workload_days.items():
        if total_days > developers[dev_id]["max_days_limit"]:
            overshoot = total_days - developers[dev_id]["max_days_limit"]
            penalty += overshoot * 10000  # Strict mathematical penalty
            
    return total_cost + penalty, dev_workload_days, total_cost

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

print("🧬 Evolutionary Optimizer running...")
for generation in range(GENERATIONS):
    # Score the population
    scored_pop = []
    for ind in population:
        score, _, _ = evaluate_schedule(ind)
        scored_pop.append((score, ind))
        
    # Sort from cheapest/best to worst
    scored_pop.sort(key=lambda x: x[0])
    
    # Selection: Keep top 20 best schedules to seed next generation
    next_generation = [ind for score, ind in scored_pop[:20]]
    
    # Crossover and Mutate to fill the rest of the pool
    while len(next_generation) < POPULATION_SIZE:
        p1, p2 = scored_pop[np.random.randint(0, 15)][1], scored_pop[np.random.randint(0, 15)][1]
        c1, c2 = crossover(p1, p2)
        next_generation.append(mutate(c1))
        if len(next_generation) < POPULATION_SIZE:
            next_generation.append(mutate(c2))
            
    population = next_generation

# ==========================================
# 4. PRINT THE OPTIMAL SCHEDULE RESULTS
# ==========================================
best_schedule = population[0]
final_score, final_workload, final_cost = evaluate_schedule(best_schedule)

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