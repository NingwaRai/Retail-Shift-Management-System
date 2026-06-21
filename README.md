# ShiftFlow - Retail Shift Management System

ShiftFlow is a modern, responsive Flask-based web application designed for retail managers to organize team rosters, assign shifts, manage departments, and track hourly staffing coverage through visual grids and an interactive donut chart wheel.

---

## Key Features

1. **Roster Management (Employees)**:
   - Add, edit, list, and delete employee profiles.
   - Store positions, contact information (phone, email), and department associations.

2. **Shift Scheduling**:
   - Schedule shifts with date, day of week, start/end times, and required roles.
   - Automatic weekday detection when a calendar date is picked.

3. **Department Management**:
   - Define business departments (e.g. Sales, Customer Support).
   - Set daily required employee numbers. The system automatically divides this target by 24 to compute the hourly staffing baseline.

4. **Staffing Coverage Dashboard**:
   - **Day View**: A side-by-side view featuring an interactive **24-Hour Coverage Donut Wheel** and a vertical hourly timeline. Slices are color-coded dynamically (Crimson: Unattended, Amber: Understaffed, Emerald: Optimal, Blue: Overstaffed). Hovering over a slice displays metrics in the center of the wheel and slides/highlights the timeline row.
   - **Week View**: A 7x24 heatmap grid mapping the entire week's coverage. Hovering over a block displays a summary of target count, coverage count, and names of scheduled employees.
   - **Month View**: A calendar layout summing daily scheduling health (understaffed, optimal, unattended, surplus hours). Click any day cell to drill down into its Day View.

---

## Technology Stack

- **Backend**: Python 3 & Flask framework.
- **Database**: SQLite 3 database (`retail_shift_management.db`).
- **Frontend**: Responsive HTML5, Vanilla CSS, and custom JavaScript with SVG-rendered vector graphics.

---

## Directory Structure

```text
├── app.py                      # Main Flask application and business routes
├── database.py                 # SQLite schema initialization and database migrations
├── requirements.txt            # Python dependencies lists
├── static/
│   └── style.css               # Core styling and dark-mode aesthetics
└── templates/
    ├── base.html               # Main layout sidebar navigation and footer
    ├── index.html              # Coverage Dashboard views (Day, Week, Month)
    ├── employees.html          # Team roster management table
    ├── add_employee.html       # Employee onboarding form
    ├── edit_employee.html      # Employee editing form
    ├── departments.html        # Department listings with action triggers
    ├── add_department.html     # Department definition form
    ├── edit_department.html    # Department modification form
    ├── shifts.html             # Weekly shifts calendar
    ├── add_shift.html          # New shift placement form
    └── edit_shift.html         # Shift editing form
```

---

## Getting Started

### Prerequisites
- Python 3 installed.
- SQLite installed (typically bundled with Python).

### Setup and Running Instructions

1. **Clone or navigate** to the project directory:
   ```bash
   cd Retail_Shift_Management_System
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Create environment
   python3 -m venv .venv

   # Activate environment (macOS/Linux)
   source .venv/bin/activate

   # Activate environment (Windows Command Prompt)
   .venv\Scripts\activate.bat
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python3 app.py
   ```

5. **Open in Browser**:
   Navigate to **`http://127.0.0.1:5001/`** in your browser.
