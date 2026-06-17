import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor

# Set page title and layout
st.set_page_config(page_title="Agile Resource Optimizer Pro", layout="wide")
st.title("🤖 Smart Agile Project Resource Optimizer")
st.write("Using Machine Learning & Genetic Algorithms to perfectly balance team workloads.")

# --- SIDEBAR CONFIGURATION (DYNAMIC UPGRADES) ---
st.sidebar.header("⚙️ GA Engine Parameters")
pop_size = st.sidebar.slider("GA Population Size", 10, 100, 50)
generations = st.sidebar.slider("GA Generations", 10, 100, 40)

st.sidebar.header("👥 Team Cost & Capacity")

# Dynamic controls for Junior Developer
st.sidebar.subheader("Junior Developer")
jr_cost = st.sidebar.number_input("Junior Cost per Day ($)", min_value=50, max_value=500, value=150, step=10)
jr_limit = st.sidebar.slider("Junior Max Capacity (Days)", 1, 10, 5)

# Dynamic controls for Mid-Level Developer
st.sidebar.subheader("Mid-Level Developer")
mid_cost = st.sidebar.number_input("Mid-Level Cost per Day ($)", min_value=100, max_value=1000, value=300, step=25)
mid_limit = st.sidebar.slider("Mid Max Capacity (Days)", 1, 10, 5)

# Dynamic controls for Senior Developer
st.sidebar.subheader("Senior Developer")
sr_cost = st.sidebar.number_input("Senior Cost per Day ($)", min_value=200, max_value=2000, value=600, step=50)
sr_limit = st.sidebar.slider("Senior Max Capacity (Days)", 1, 10, 5)

# Update the developer pool dictionary with sidebar values dynamically
developers = {
    0: {"name": "Junior Developer", "cost_per_day": jr_cost, "max_days_limit": jr_limit},
    1: {"name": "Mid-Level Developer", "cost_per_day": mid_cost, "max_days_limit": mid_limit},
    2: {"name": "Senior Developer", "cost_per_day": sr_cost, "max_days_limit": sr_limit}
}

# --- LOAD DATA & TRAIN MODEL ---
@st.cache_resource
def load_and_train():
    df = pd.read_csv('cleaned_dataset.csv')
    X = df.drop(columns=['Number', 'Time Taken (days)', 'User'])
    y = df['Time Taken (days)'].astype(float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model, X_test

ml_model, X_test = load_and_train()

# Select Tasks
st.subheader("📋 Upcoming Tasks in Sprint Pool")
num_tasks_to_pick = st.number_input("Select number of tasks to pull for this sprint:", min_value=3, max_value=15, value=8)
new_tasks_pool = X_test.head(int(num_tasks_to_pick))
st.dataframe(new_tasks_pool)

# --- RUN OPTIMIZATION ---
if st.button("🚀 Run Evolutionary Optimization Loop", type="primary"):
    num_tasks = len(new_tasks_pool)
    num_devs = len(developers)

    def evaluate_schedule(chromosome):
        dev_workload_days = {i: 0 for i in range(num_devs)}
        total_cost = 0
        for task_idx, dev_id in enumerate(chromosome):
            task_features = new_tasks_pool.iloc[[task_idx]]
            predicted_days = float(ml_model.predict(task_features)[0])
            dev_workload_days[dev_id] += predicted_days
            total_cost += predicted_days * developers[dev_id]["cost_per_day"]
        
        # Applying dynamic limits from sidebar to the penalty calculation
        penalty = 0
        for dev_id, total_days in dev_workload_days.items():
            if total_days > developers[dev_id]["max_days_limit"]:
                penalty += (total_days - developers[dev_id]["max_days_limit"]) * 10000
        return total_cost + penalty, dev_workload_days, total_cost

    # GA Operators
    population = [list(np.random.randint(0, num_devs, size=num_tasks)) for _ in range(pop_size)]
    
    for _ in range(generations):
        scored_pop = [(evaluate_schedule(ind)[0], ind) for ind in population]
        scored_pop.sort(key=lambda x: x[0])
        next_gen = [ind for _, ind in scored_pop[:20]]
        while len(next_gen) < pop_size:
            p1, p2 = scored_pop[np.random.randint(0, 15)][1], scored_pop[np.random.randint(0, 15)][1]
            pt = np.random.randint(1, num_tasks - 1)
            c1 = p1[:pt] + p2[pt:]
            next_gen.append(c1)
        population = next_gen[:pop_size]

    best_schedule = population[0]
    _, final_workload, final_cost = evaluate_schedule(best_schedule)

    # Display Results
    st.success("🏆 Optimization Complete!")
    
    # 3-Column structural breakdown layout
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Total Optimized Sprint Cost", value=f"${final_cost:,.2f}")
        st.subheader("📍 Task Allocation Mapping")
        assignment_data = []
        for task_idx, dev_id in enumerate(best_schedule):
            assignment_data.append({"Task": f"Task #{task_idx+1}", "Assigned Engineer": developers[dev_id]['name']})
        st.table(pd.DataFrame(assignment_data))

    with col2:
        st.subheader("📊 Team Workload Balance")
        
        # Create workload data frame
        chart_data = pd.DataFrame({
            "Developer": [developers[d]['name'] for d in final_workload.keys()],
            "Predicted Work (Days)": list(final_workload.values()),
            "Max Capacity Limit": [developers[d]['max_days_limit'] for d in final_workload.keys()]
        })
        
        # Build bar chart with Plotly
        fig_bar = px.bar(chart_data, x="Developer", y="Predicted Work (Days)", color="Developer", text_auto='.2f')
        
        # Visual Upgrade: Add horizontal line indicating task threshold limits dynamically!
        for d in final_workload.keys():
            fig_bar.add_hline(y=developers[d]['max_days_limit'], line_dash="dash", line_color="red", 
                              annotation_text=f"{developers[d]['name']} Limit", annotation_position="top left")
            
        st.plotly_chart(fig_bar, use_container_width=True)

    with col3:
        st.subheader("🍕 Financial Cost Allocation")
        
        # Calculate how much budget went to each specific developer tier
        financial_data = pd.DataFrame({
            "Developer": [developers[d]['name'] for d in final_workload.keys()],
            "Cost Split ($)": [final_workload[d] * developers[d]['cost_per_day'] for d in final_workload.keys()]
        })
        
        # Build elegant financial allocation Pie Chart
        fig_pie = px.pie(financial_data, values="Cost Split ($)", names="Developer", 
                         color="Developer", hole=0.4, title="Budget Distribution Percentage")
        st.plotly_chart(fig_pie, use_container_width=True)