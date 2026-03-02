#!/usr/bin/env python3
"""
Advanced Todo Application - Python Command Line Version
Features: Categories, Priorities, Due Dates, Local Storage, Export/Import
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import argparse
import sys
from dataclasses import dataclass, asdict
from enum import Enum


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"


@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    category: str = "personal"
    priority: Priority = Priority.MEDIUM
    completed: bool = False
    created_at: str = ""
    due_date: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    @property
    def status(self) -> Status:
        if self.completed:
            return Status.COMPLETED
        elif self.due_date and datetime.fromisoformat(self.due_date) < datetime.now():
            return Status.OVERDUE
        return Status.PENDING
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        data = data.copy()
        data['priority'] = Priority(data['priority'])
        return cls(**data)


class TodoApp:
    def __init__(self, data_file: str = "tasks.json"):
        self.data_file = data_file
        self.tasks: List[Task] = []
        self.next_id = 1
        self.categories = ["personal", "work", "shopping", "health"]
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(task_data) for task_data in data.get('tasks', [])]
                    self.next_id = data.get('next_id', 1)
                    self.categories = data.get('categories', self.categories)
                print(f"✅ Loaded {len(self.tasks)} tasks from {self.data_file}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"❌ Error loading tasks: {e}")
                self.tasks = []
    
    def save_tasks(self):
        """Save tasks to JSON file."""
        try:
            data = {
                'tasks': [task.to_dict() for task in self.tasks],
                'next_id': self.next_id,
                'categories': self.categories,
                'saved_at': datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved {len(self.tasks)} tasks to {self.data_file}")
        except Exception as e:
            print(f"❌ Error saving tasks: {e}")
    
    def add_task(self, title: str, description: str = "", category: str = "personal", 
                 priority: str = "medium", due_date: Optional[str] = None) -> Task:
        """Add a new task."""
        task = Task(
            id=self.next_id,
            title=title,
            description=description,
            category=category,
            priority=Priority(priority),
            due_date=due_date
        )
        
        self.tasks.insert(0, task)  # Add to beginning like JavaScript version
        self.next_id += 1
        self.save_tasks()
        
        print(f"✅ Added task: '{title}'")
        return task
    
    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed."""
        task = self.get_task_by_id(task_id)
        if task:
            task.completed = True
            self.save_tasks()
            print(f"✅ Completed task: '{task.title}'")
            return True
        print(f"❌ Task with ID {task_id} not found")
        return False
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        task = self.get_task_by_id(task_id)
        if task:
            self.tasks.remove(task)
            self.save_tasks()
            print(f"🗑️ Deleted task: '{task.title}'")
            return True
        print(f"❌ Task with ID {task_id} not found")
        return False
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return next((task for task in self.tasks if task.id == task_id), None)
    
    def list_tasks(self, category: Optional[str] = None, status: Optional[str] = None,
                   priority: Optional[str] = None, search: Optional[str] = None) -> List[Task]:
        """List tasks with optional filters."""
        filtered_tasks = self.tasks.copy()
        
        # Apply filters
        if category and category != "all":
            filtered_tasks = [t for t in filtered_tasks if t.category == category]
        
        if status:
            if status == "completed":
                filtered_tasks = [t for t in filtered_tasks if t.completed]
            elif status == "pending":
                filtered_tasks = [t for t in filtered_tasks if not t.completed]
            elif status == "overdue":
                filtered_tasks = [t for t in filtered_tasks if t.status == Status.OVERDUE]
        
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t.priority.value == priority]
        
        if search:
            search_lower = search.lower()
            filtered_tasks = [
                t for t in filtered_tasks 
                if search_lower in t.title.lower() or search_lower in t.description.lower()
            ]
        
        return filtered_tasks
    
    def display_tasks(self, tasks: List[Task], detailed: bool = False):
        """Display tasks in formatted output."""
        if not tasks:
            print("📝 No tasks found.")
            return
        
        print(f"\n📋 Found {len(tasks)} task(s):")
        print("=" * 80)
        
        for task in tasks:
            status_icon = "✅" if task.completed else ("⚠️" if task.status == Status.OVERDUE else "⏳")
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[task.priority.value]
            
            print(f"{status_icon} [{task.id}] {task.title}")
            
            if detailed:
                print(f"   📂 Category: {task.category.title()}")
                print(f"   {priority_icon} Priority: {task.priority.value.title()}")
                
                if task.description:
                    print(f"   📄 Description: {task.description}")
                
                if task.due_date:
                    due = datetime.fromisoformat(task.due_date)
                    print(f"   📅 Due: {due.strftime('%Y-%m-%d %H:%M')}")
                
                created = datetime.fromisoformat(task.created_at)
                print(f"   🕒 Created: {created.strftime('%Y-%m-%d %H:%M')}")
                print()
    
    def get_stats(self) -> Dict[str, int]:
        """Get task statistics."""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.completed])
        pending = total - completed
        overdue = len([t for t in self.tasks if t.status == Status.OVERDUE])
        
        # Category counts
        category_counts = {}
        for category in self.categories:
            category_counts[category] = len([t for t in self.tasks if t.category == category])
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'overdue': overdue,
            'categories': category_counts
        }
    
    def display_stats(self):
        """Display task statistics."""
        stats = self.get_stats()
        
        print("\n📊 Task Statistics:")
        print("=" * 40)
        print(f"📝 Total Tasks: {stats['total']}")
        print(f"✅ Completed: {stats['completed']}")
        print(f"⏳ Pending: {stats['pending']}")
        print(f"⚠️ Overdue: {stats['overdue']}")
        
        print(f"\n📂 By Category:")
        for category, count in stats['categories'].items():
            print(f"   {category.title()}: {count}")
    
    def export_tasks(self, filename: str = None) -> str:
        """Export tasks to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tasks_export_{timestamp}.json"
        
        export_data = {
            'tasks': [task.to_dict() for task in self.tasks],
            'categories': self.categories,
            'export_date': datetime.now().isoformat(),
            'total_tasks': len(self.tasks)
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📤 Exported {len(self.tasks)} tasks to {filename}")
        return filename
    
    def import_tasks(self, filename: str) -> int:
        """Import tasks from JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            imported_tasks = [Task.from_dict(task_data) for task_data in data.get('tasks', [])]
            
            # Update IDs to avoid conflicts
            for task in imported_tasks:
                task.id = self.next_id
                self.next_id += 1
            
            self.tasks.extend(imported_tasks)
            self.save_tasks()
            
            print(f"📥 Imported {len(imported_tasks)} tasks from {filename}")
            return len(imported_tasks)
            
        except Exception as e:
            print(f"❌ Error importing tasks: {e}")
            return 0


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(description="Advanced Todo Application")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add task
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('title', help='Task title')
    add_parser.add_argument('-d', '--description', default='', help='Task description')
    add_parser.add_argument('-c', '--category', default='personal', 
                           choices=['personal', 'work', 'shopping', 'health'],
                           help='Task category')
    add_parser.add_argument('-p', '--priority', default='medium',
                           choices=['low', 'medium', 'high'],
                           help='Task priority')
    add_parser.add_argument('--due', help='Due date (YYYY-MM-DD HH:MM)')
    
    # List tasks
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('-c', '--category', help='Filter by category')
    list_parser.add_argument('-s', '--status', choices=['completed', 'pending', 'overdue'],
                            help='Filter by status')
    list_parser.add_argument('-p', '--priority', choices=['low', 'medium', 'high'],
                            help='Filter by priority')
    list_parser.add_argument('--search', help='Search in title and description')
    list_parser.add_argument('--detailed', action='store_true', help='Show detailed information')
    
    # Complete task
    complete_parser = subparsers.add_parser('complete', help='Mark task as completed')
    complete_parser.add_argument('id', type=int, help='Task ID')
    
    # Delete task
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('id', type=int, help='Task ID')
    
    # Statistics
    subparsers.add_parser('stats', help='Show task statistics')
    
    # Export tasks
    export_parser = subparsers.add_parser('export', help='Export tasks to file')
    export_parser.add_argument('-f', '--file', help='Export filename')
    
    # Import tasks
    import_parser = subparsers.add_parser('import', help='Import tasks from file')
    import_parser.add_argument('file', help='Import filename')
    
    return parser


def main():
    """Main application entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    app = TodoApp()
    
    try:
        if args.command == 'add':
            due_date = None
            if args.due:
                try:
                    due_date = datetime.strptime(args.due, '%Y-%m-%d %H:%M').isoformat()
                except ValueError:
                    try:
                        due_date = datetime.strptime(args.due, '%Y-%m-%d').isoformat()
                    except ValueError:
                        print("❌ Invalid due date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM")
                        return
            
            app.add_task(args.title, args.description, args.category, args.priority, due_date)
        
        elif args.command == 'list':
            tasks = app.list_tasks(args.category, args.status, args.priority, args.search)
            app.display_tasks(tasks, args.detailed)
        
        elif args.command == 'complete':
            app.complete_task(args.id)
        
        elif args.command == 'delete':
            app.delete_task(args.id)
        
        elif args.command == 'stats':
            app.display_stats()
        
        elif args.command == 'export':
            app.export_tasks(args.file)
        
        elif args.command == 'import':
            app.import_tasks(args.file)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()