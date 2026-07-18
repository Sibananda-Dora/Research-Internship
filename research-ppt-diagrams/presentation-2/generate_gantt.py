import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Define the updated tasks based on the WhatsApp image flow and user feedback
tasks = [
    "Problem Formulation\n& Literature Study",
    "Architecture &\nRequirement Design",
    "Data Acquisition\n& Harmonization",
    "Core Machine Learning\nDevelopment",
    "Virtual Digital Twin\nImplementation",
    "Dashboard UI\n& GIS Integration",
    "Simulation &\nSystem Testing",
    "Final Deployment\n& Report Writing"
]

# Start week and duration (x-axis goes 0 to 6)
# Mimicking the waterfall flow from the WhatsApp image
start_weeks = [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0]
durations =   [1.5, 1.5, 1.5, 2.0, 1.5, 1.5, 1.0, 1.0]

def create_excel_gantt():
    fig, ax = plt.subplots(figsize=(11, 7))
    
    ax.set_axisbelow(True)
    ax.set_facecolor('#ffffff')
    fig.patch.set_facecolor('#ffffff')

    # Draw grid lines at integers (0, 1, 2... 6) to form 6 columns
    ax.set_xticks(range(7), minor=True)
    ax.xaxis.grid(True, which='minor', color='gray', linestyle='dashed', linewidth=0.5)
    ax.yaxis.grid(True, color='gray', linestyle='solid', linewidth=0.5)
    
    # Put labels in the center of the columns (0.5, 1.5... 5.5)
    ax.set_xticks(np.arange(0.5, 6.5, 1))
    ax.set_xticklabels([f"Week {i}" for i in range(1, 7)], fontsize=11, fontweight='bold')
    ax.xaxis.grid(False, which='major')

    # Classic Office colors mapping to the 8 tasks
    colors = ['#C0504D', '#4F81BD', '#9BBB59', '#8064A2', '#F79646', '#4BACC6', '#C0504D', '#8064A2']
    
    for i, (task, start, duration, color) in enumerate(zip(tasks, start_weeks, durations, colors)):
        ax.barh(i, duration, left=start, height=0.6, align='center', color=color, edgecolor='black', zorder=3)
        
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t.replace('\n', ' ') for t in tasks], fontsize=11)
    ax.invert_yaxis()
    
    ax.set_xlim(0, 6)
    ax.set_title("6-Week Research & Implementation Gantt Chart", fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig('Gantt_Excel_Style.png', dpi=300)
    plt.close()

def create_ppt_gantt():
    bg_color = '#7293D6' 
    content_color = '#FFFFFF'
    
    # Custom modern pastel colors for the 8 tasks
    accent_colors = ['#F5B7B1', '#AED6F1', '#A9DFBF', '#D2B4DE', '#F9E79F', '#A3E4D7', '#F5CBA7', '#D2B4DE']
    
    fig, ax = plt.subplots(figsize=(13, 9))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    
    # Hide standard spines
    for spine in ax.spines.values():
        spine.set_edgecolor('none')
        
    # Draw the main white rounded background covering the plotting area
    rect = patches.FancyBboxPatch((-0.2, -0.8), 6.4, len(tasks)+0.2, 
                                  boxstyle="round,pad=0.2,rounding_size=0.2", 
                                  fc=content_color, ec='none', zorder=1)
    ax.add_patch(rect)
    
    # Draw column separator lines
    ax.set_xticks(range(7), minor=True)
    ax.xaxis.grid(True, which='minor', color='#E5E7E9', linestyle='-', linewidth=1.5, zorder=2)
    ax.yaxis.grid(False)
    
    # Center labels
    ax.set_xticks(np.arange(0.5, 6.5, 1))
    ax.set_xticklabels([f"Week {i}" for i in range(1, 7)], fontsize=14, fontweight='bold', color='#1C2833')
    ax.xaxis.grid(False, which='major')

    for i, (task, start, duration, color) in enumerate(zip(tasks, start_weeks, durations, accent_colors)):
        # Draw rounded bar using FancyBboxPatch for modern UI look
        p = patches.FancyBboxPatch((start+0.05, i - 0.35), duration-0.1, 0.7, 
                                   boxstyle="round,pad=0.05,rounding_size=0.15", 
                                   fc=color, ec='#34495E', lw=1.2, zorder=3)
        ax.add_patch(p)
        
        # Add text inside the bar
        ax.text(start + duration/2, i, task, va='center', ha='center', 
                color='#1C2833', fontsize=11, fontweight='bold', zorder=4)

    ax.set_yticks([]) 
    ax.invert_yaxis()
    ax.set_xlim(0, 6)
    ax.set_title("6-Week Research & Implementation Gantt Chart", fontsize=24, fontweight='bold', color='#FFFFFF', pad=25)
    
    plt.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05)
    plt.savefig('Gantt_PPT_Theme.png', dpi=300, facecolor=bg_color, edgecolor='none')
    plt.close()

if __name__ == "__main__":
    create_excel_gantt()
    create_ppt_gantt()
    print("Updated images with 8 tasks generated successfully.")
