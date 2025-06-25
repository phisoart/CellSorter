#!/usr/bin/env python3
"""
Generate TaskMaster Progress Chart

Creates a visual progress chart for the CellSorter project tasks.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

def load_tasks():
    """Load tasks from TaskMaster JSON file."""
    tasks_file = Path(".taskmaster/tasks/tasks.json")
    if not tasks_file.exists():
        print("TaskMaster tasks.json not found!")
        return None
    
    with open(tasks_file, 'r') as f:
        return json.load(f)

def create_progress_chart():
    """Create and save a progress chart."""
    data = load_tasks()
    if not data:
        return
    
    # Extract data
    tasks = data['tasks']
    metadata = data['metadata']
    
    # Count by status
    completed = sum(1 for task in tasks if task['status'] == 'completed')
    todo = sum(1 for task in tasks if task['status'] == 'todo')
    total = len(tasks)
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('CellSorter TaskMaster Progress Dashboard', fontsize=16, fontweight='bold')
    
    # 1. Overall Progress Pie Chart
    ax1.pie([completed, todo], labels=['Completed', 'Remaining'], 
            colors=['#2E8B57', '#DC143C'], autopct='%1.1f%%', startangle=90)
    ax1.set_title(f'Overall Progress\n{completed}/{total} Tasks Complete')
    
    # 2. Status Bar Chart
    statuses = ['Completed', 'Todo']
    counts = [completed, todo]
    colors = ['#2E8B57', '#DC143C']
    ax2.bar(statuses, counts, color=colors)
    ax2.set_title('Task Status Distribution')
    ax2.set_ylabel('Number of Tasks')
    for i, v in enumerate(counts):
        ax2.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
    
    # 3. Priority Breakdown
    priority_counts = metadata['by_priority']
    priorities = list(priority_counts.keys())
    priority_values = list(priority_counts.values())
    colors_priority = ['#FF6B6B', '#FFE66D', '#4ECDC4']
    ax3.bar(priorities, priority_values, color=colors_priority)
    ax3.set_title('Tasks by Priority')
    ax3.set_ylabel('Number of Tasks')
    for i, v in enumerate(priority_values):
        ax3.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
    
    # 4. Task Timeline/Gantt-style view
    completed_tasks = [task for task in tasks if task['status'] == 'completed']
    todo_tasks = [task for task in tasks if task['status'] == 'todo']
    
    y_pos = range(len(tasks))
    colors_gantt = ['#2E8B57' if task['status'] == 'completed' else '#DC143C' for task in tasks]
    
    ax4.barh(y_pos, [1] * len(tasks), color=colors_gantt, alpha=0.7)
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels([f"TASK-{task['id'].split('-')[1]}: {task['title'][:30]}..." 
                         if len(task['title']) > 30 else f"TASK-{task['id'].split('-')[1]}: {task['title']}" 
                         for task in tasks], fontsize=8)
    ax4.set_xlabel('Status')
    ax4.set_title('Task Status Overview')
    ax4.set_xlim(0, 1)
    
    # Add legend
    completed_patch = patches.Patch(color='#2E8B57', label='Completed')
    todo_patch = patches.Patch(color='#DC143C', label='Todo')
    ax4.legend(handles=[completed_patch, todo_patch], loc='lower right')
    
    plt.tight_layout()
    plt.savefig('taskmaster_progress.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Progress chart saved as 'taskmaster_progress.png'")
    print(f"Overall Progress: {completed}/{total} tasks completed ({100*completed/total:.1f}%)")

def print_ascii_progress():
    """Print ASCII progress bar to console."""
    data = load_tasks()
    if not data:
        return
    
    completed = sum(1 for task in data['tasks'] if task['status'] == 'completed')
    total = len(data['tasks'])
    percentage = completed / total
    
    # Create ASCII progress bar
    bar_length = 20
    filled_length = int(bar_length * percentage)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print("\n" + "="*60)
    print("🚀 CELLSORTER TASKMASTER PROGRESS DASHBOARD 🚀")
    print("="*60)
    print(f"Progress: [{bar}] {percentage:.1%} ({completed}/{total})")
    print(f"Status: {completed} Completed, {total-completed} Remaining")
    print("="*60)
    
    # Show completed tasks
    print("\n✅ COMPLETED TASKS:")
    for task in data['tasks']:
        if task['status'] == 'completed':
            print(f"  • {task['id']}: {task['title']}")
    
    # Show next tasks
    print("\n🔄 NEXT TASKS:")
    high_priority_todo = [task for task in data['tasks'] 
                          if task['status'] == 'todo' and task['priority'] == 'high']
    for task in high_priority_todo[:3]:  # Show top 3
        print(f"  • {task['id']}: {task['title']}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print_ascii_progress()
    
    # Try to create graphical chart
    try:
        create_progress_chart()
    except ImportError:
        print("\nMatplotlib not available for graphical chart.")
        print("Install with: pip install matplotlib")
    except Exception as e:
        print(f"Error creating chart: {e}")