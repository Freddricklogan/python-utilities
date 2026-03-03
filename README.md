# Python Utilities

Three standalone Python command-line tools for everyday tasks.

## Tools

### Blog Manager (`blog_manager.py`)
Manage a local blog from the terminal. Create, edit, list, search, and export posts as markdown or JSON. Posts are stored locally in JSON format with tagging and category support.

```bash
python3 blog_manager.py create "My First Post" --category tech --tags python,cli
python3 blog_manager.py list --category tech
python3 blog_manager.py search "python"
python3 blog_manager.py export --format markdown
```

### Todo App (`todo_app.py`)
Task manager with priorities, categories, due dates, and filtering. Supports import/export for backup and sharing.

```bash
python3 todo_app.py add "Finish report" --priority high --category work --due "2026-03-15"
python3 todo_app.py list --status pending --priority high
python3 todo_app.py complete 1
python3 todo_app.py stats
python3 todo_app.py export -f backup.json
```

**Priority levels:** low, medium, high
**Categories:** personal, work, shopping, health
**Filters:** status (pending/completed/overdue), priority, category, text search

### Weather App (`weather_app.py`)
Weather dashboard with current conditions, hourly/daily forecasts, air quality data, and saved locations. Supports Celsius and Fahrenheit.

```bash
python3 weather_app.py get "New York"
python3 weather_app.py get "Tokyo" --brief
python3 weather_app.py add "London"        # Save a location
python3 weather_app.py saved               # Check all saved cities
python3 weather_app.py units               # Toggle C/F
```

**Supported cities:** New York, London, Tokyo, Paris, Sydney, Berlin, Moscow, Toronto, Los Angeles, Chicago

## Setup

```bash
git clone https://github.com/Freddricklogan/python-utilities.git
cd python-utilities
```

No external dependencies required -- all tools use Python standard library plus `requests` for the weather app.

**Requirements:** Python 3.6+

## License

MIT
