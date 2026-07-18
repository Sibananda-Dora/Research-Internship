import matplotlib.pyplot as plt
import matplotlib.patches as patches

tasks = [
    "Problem Formulation & Literature Study",
    "Architecture & Requirement Design",
    "Data Acquisition & Harmonization",
    "Core Machine Learning Development",
    "Virtual Digital Twin Implementation",
    "Dashboard UI & GIS Integration",
    "Simulation & System Testing",
    "Final Deployment & Report Writing"
]

# Starts and durations mapped to cascade smoothly across 6 weeks
start_weeks = [0.0, 0.8, 1.5, 2.5, 3.5, 4.2, 4.5, 5.2]
durations =   [4.0, 1.0, 1.5, 1.5, 1.2, 1.0, 1.0, 0.8]

# Distinct Corporate Palette (Monochromatic Blues and Sleek Greys) - NO RAINBOW
colors = ['#85C1E9', '#3498DB', '#1B4F72', '#D5D8DC', '#808B96', '#2E4053', '#F39C12', '#212F3D']

fig, ax = plt.subplots(figsize=(14, 6))

# X from -3 to 6 (left column is width 3 for text)
ax.set_xlim(-3, 6)
# Y goes from -1 (header) down to len(tasks)
ax.set_ylim(len(tasks), -1)

# Hide default axes completely
ax.axis('off')

# 1. Draw header background (Corporate Midnight Blue)
header_rect = patches.Rectangle((-3, -1), 9, 1, facecolor='#152A47', edgecolor='none')
ax.add_patch(header_rect)

# 2. Draw header text
ax.text(-1.5, -0.5, "Task / Activity", color='white', fontweight='bold', fontsize=12, ha='center', va='center')

for i in range(6):
    days_text = f"({i*7+1}-{(i+1)*7} Days)"
    ax.text(i + 0.5, -0.6, f"Week {i+1}", color='white', fontweight='bold', fontsize=12, ha='center', va='center')
    ax.text(i + 0.5, -0.25, days_text, color='#AAB7B8', fontsize=10, ha='center', va='center')

# 3. Draw grid lines
# Horizontal grid lines (light grey)
for i in range(len(tasks) + 1):
    ax.plot([-3, 6], [i, i], color='#E5E8E8', linewidth=1.5, zorder=1)

# Vertical grid lines (dashed for weeks)
for i in range(7):
    # Week separators are dashed
    if i > 0 and i < 6:
        ax.plot([i, i], [-1, len(tasks)], color='#E5E8E8', linewidth=1.5, linestyle='--', zorder=1)
    elif i == 6:
        # Right edge solid
        ax.plot([i, i], [-1, len(tasks)], color='#E5E8E8', linewidth=1.5, zorder=1)

# Vertical lines for left column
ax.plot([0, 0], [-1, len(tasks)], color='#152A47', linewidth=2.0, zorder=1) # Divides text and chart
ax.plot([-3, -3], [-1, len(tasks)], color='#E5E8E8', linewidth=1.5, zorder=1) # Leftmost edge

# 4. Draw Tasks and Flat Bars
for i, (task, start, duration, color) in enumerate(zip(tasks, start_weeks, durations, colors)):
    # Task text
    ax.text(-2.8, i + 0.5, task, color='#17202A', fontsize=11, fontweight='bold', va='center', ha='left')
    
    # Flat color bar (no text inside, no border)
    bar_rect = patches.Rectangle((start, i + 0.25), duration, 0.5, facecolor=color, edgecolor='none', zorder=2)
    ax.add_patch(bar_rect)

plt.tight_layout()
# Save as a NEW file name to bypass any system caching
plt.savefig('Gantt_Classic_Corporate.png', dpi=300, bbox_inches='tight')
plt.close()
print("Corporate style Gantt chart generated successfully.")
