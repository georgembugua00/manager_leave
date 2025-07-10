# manager_view.py
import streamlit as st
from datetime import date, timedelta, datetime

# database_utils.py
import sqlite3
from datetime import datetime, date, timedelta

# DATABASE PATH - IMPORTANT: Update this to your actual database file path
DATABASE_PATH = '/Users/danielwanganga/Documents/Airtel_AI/leave_management.db'

def init_db():
    """Initializes the SQLite database and creates necessary tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Create employees table if it doesn't exist (assuming 'id' is employee_id)
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            surname TEXT,
            partner TEXT NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            salary INTEGER NOT NULL,
            profile_pic TEXT
        )
    ''')

    # Create leave_entitlements table
    c.execute('''
        CREATE TABLE IF NOT EXISTS leave_entitlements (
            employee_id TEXT PRIMARY KEY,
            annual_leave INTEGER NOT NULL,
            sick_leave INTEGER NOT NULL,
            compensation_leave INTEGER NOT NULL,
            maternity_leave_days INTEGER NOT NULL,
            paternity_leave_days INTEGER NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')

    # Re-introducing the 'leaves' table for leave applications, linked to employees
    # IMPORTANT: If you modified your schema and had a 'DROP TABLE IF EXISTS leaves' before,
    # make sure your database is updated to the latest schema, then you can remove the DROP.
    # For initial setup or schema updates, you might temporarily uncomment DROP TABLE.
    # c.execute('DROP TABLE IF EXISTS leaves') # Uncomment ONLY if you need to reset the leaves table structure

    c.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            description TEXT,
            attachment BOOLEAN,
            status TEXT NOT NULL,
            decline_reason TEXT,
            recall_reason TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_employee_by_name(employee_name):
    """Fetches employee details by name."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, name FROM employees WHERE name = ? COLLATE NOCASE", (employee_name,))
    employee = c.fetchone()
    conn.close()
    return employee

def apply_for_leave(employee_id, leave_type, start_date, end_date, description, attachment):
    """Adds a new leave application to the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO leaves (employee_id, leave_type, start_date, end_date, description, attachment, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    ''', (employee_id, leave_type, start_date.isoformat(), end_date.isoformat(), description, bool(attachment)))
    conn.commit()
    conn.close()

def get_leave_history(employee_id):
    """Fetches the leave history for a specific employee."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT leave_type, start_date, end_date, description, status, decline_reason, recall_reason FROM leaves WHERE employee_id = ?", (employee_id,))
    history = c.fetchall()
    conn.close()
    return history

def get_all_pending_leaves():
    """Fetches all leave requests with a 'Pending' status for the manager."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT l.id, e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'Pending'
    """)
    pending_leaves = c.fetchall()
    conn.close()
    return pending_leaves

def get_approved_leaves():
    """Fetches all leave requests with an 'Approved' status, including dates for recall logic."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT l.id, e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'Approved'
    """)
    approved_leaves = c.fetchall()
    conn.close()
    return approved_leaves

def update_leave_status(leave_id, new_status, reason=None):
    """Updates the status of a leave request (Approve, Decline, Recall)."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    if new_status == "Declined":
        c.execute("UPDATE leaves SET status = ?, decline_reason = ? WHERE id = ?", (new_status, reason, leave_id))
    elif new_status == "Recalled":
        c.execute("UPDATE leaves SET status = ?, recall_reason = ? WHERE id = ?", (new_status, reason, leave_id))
    else: # Approved
        c.execute("UPDATE leaves SET status = ? WHERE id = ?", (new_status, leave_id))
    conn.commit()
    conn.close()

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """Fetches all team leaves with optional filters for the manager's dashboard."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    query = """
        SELECT e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.status, l.description, l.decline_reason
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        placeholders = ','.join('?' * len(status_filter))
        query += f" AND l.status IN ({placeholders})"
        params.extend(status_filter)
    if leave_type_filter:
        placeholders = ','.join('?' * len(leave_type_filter))
        query += f" AND l.leave_type IN ({placeholders})"
        params.extend(leave_type_filter)
    if employee_filter and employee_filter != "All Team Members":
        query += " AND e.name = ?"
        params.append(employee_filter)
    c.execute(query, params)
    leaves = c.fetchall()
    conn.close()
    return leaves

def get_all_employees_from_db():
    """Gets a unique list of all employees from the employees table."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT name FROM employees ORDER BY name")
    employees = [row[0] for row in c.fetchall()]
    conn.close()
    return employees

def get_all_leaves():
    """Fetches all leave records, joining with employee names."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT l.id, e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description, l.status
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
    """)
    rows = c.fetchall()
    conn.close()
    leaves = []
    for row in rows:
        leaves.append({
            "id": row["id"],
            "name": row["employee_name"],
            "type": row["leave_type"],
            "start": row["start_date"],
            "end": row["end_date"],
            "description": row["description"],
            "status": row["status"]
        })
    return leaves

def withdraw_leave(leave_id, recall_reason=None):
    """Marks a leave request as Withdrawn with an optional reason."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("UPDATE leaves SET status = 'Withdrawn', recall_reason = ? WHERE id = ?", (recall_reason, leave_id))
    conn.commit()
    conn.close()

def get_latest_leave_entry():
    """Fetches the details of the most recently added leave entry."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description, l.status, l.decline_reason, l.recall_reason
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        ORDER BY l.id DESC LIMIT 1
    """)
    latest_entry = c.fetchone()
    conn.close()
    return latest_entry

def get_employee_leave_entitlements(employee_id):
    """Fetches leave entitlements for a given employee."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM leave_entitlements WHERE employee_id = ?", (employee_id,))
    entitlements = c.fetchone()
    conn.close()
    return entitlements

def get_employee_used_leave(employee_id, leave_type=None):
    """Calculates total used leave days for an employee, optionally by type."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    query = "SELECT SUM(JULIANDAY(end_date) - JULIANDAY(start_date) + 1) FROM leaves WHERE employee_id = ? AND status = 'Approved'"
    params = [employee_id]
    if leave_type:
        query += " AND leave_type = ?"
        params.append(leave_type)
    c.execute(query, params)
    used_days = c.fetchone()[0]
    conn.close()
    return int(used_days) if used_days else 0

# Initialize DB (ensure this runs only once per session)
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

st.set_page_config(layout="wide") # Use wide layout for better display

st.html("""
<style>
    .header-style {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .header-style h1 {
        color: #2c3e50;
        font-size: 2.5em;
        margin-bottom: 5px;
    }
    .header-style p {
        color: #7f8c8d;
        font-size: 1.1em;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stButton>button[key*="decline"] {
        background-color: #e74c3c;
    }
    .stButton>button[key*="decline"]:hover {
        background-color: #c0392b;
    }
    .stButton>button[key*="recall"] { /* New style for recall button */
        background-color: #f39c12; /* Orange */
    }
    .stButton>button[key*="recall"]:hover {
        background-color: #e67e22; /* Darker orange */
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
</style>
<div class="header-style">
    <h1>📅 Leave Request Manager</h1>
    <p style="margin: 0; opacity: 0.9;">Review and manage employee leave requests</p>
</div>
""")

def pending_leaves_view():
    st.header("Pending Leave Requests for Review")
    pending_leaves = get_all_pending_leaves()

    if not pending_leaves:
        st.success("✨ All caught up! There are no pending leave requests.")
        return

    for leave in pending_leaves:
        # Access by key name since row_factory is set to sqlite3.Row
        leave_id = leave["id"]
        employee = leave["employee_name"]
        leave_type = leave["leave_type"]
        start_date = leave["start_date"]
        end_date = leave["end_date"]
        description = leave["description"]

        with st.expander(f"Request from {employee} ({leave_type}) - {start_date} to {end_date}", expanded=True):
            st.write(f"**Employee:** {employee}")
            st.write(f"**Leave Type:** {leave_type}")
            st.write(f"**Dates:** {start_date} to {end_date}")
            st.write(f"**Reason:** {description}")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ Approve", key=f"approve_{leave_id}"):
                    update_leave_status(leave_id, "Approved")
                    st.success(f"Leave for {employee} approved.")
                    st.rerun()
            with col2:
                if st.button("❌ Decline", key=f"decline_{leave_id}"):
                    if f"show_reason_{leave_id}" not in st.session_state:
                        st.session_state[f"show_reason_{leave_id}"] = False
                    st.session_state[f"show_reason_{leave_id}"] = not st.session_state[f"show_reason_{leave_id}"]

                    if st.session_state[f"show_reason_{leave_id}"]:
                        decline_reason = st.text_input("Reason for declining:", key=f"reason_{leave_id}")
                        if st.button("Confirm Decline", key=f"confirm_decline_{leave_id}"):
                            if decline_reason:
                                update_leave_status(leave_id, "Declined", reason=decline_reason)
                                st.error(f"Leave for {employee} declined.")
                                st.rerun()
                            else:
                                st.warning("A reason is required to decline a request.")

from datetime import datetime, date

def approved_leaves_for_recall_view():
    st.header("Approved Leaves (for Recall)")
    approved_leaves = get_approved_leaves()

    if not approved_leaves:
        st.info("No approved leaves currently.")
        return

    for leave in approved_leaves:
        leave_id = leave["id"]
        employee = leave["employee_name"]
        leave_type = leave["leave_type"]
        start_date_str = leave["start_date"]
        end_date_str = leave["end_date"]
        description = leave["description"]

        # Safe date parsing
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            st.error(f"⚠️ Invalid date format in leave ID {leave_id} for {employee}: {start_date_str} to {end_date_str}")
            continue  # Skip this entry

        today = date.today()

        # Calculate remaining days
        if today > end_date:
            days_left = 0
        elif today < start_date:
            days_left = (end_date - start_date).days + 1
        else:
            days_left = (end_date - today).days + 1

        with st.expander(f"Approved Leave for {employee} ({leave_type}) - {start_date_str} to {end_date_str}", expanded=True):
            st.write(f"**Employee:** {employee}")
            st.write(f"**Leave Type:** {leave_type}")
            st.write(f"**Dates:** {start_date_str} to {end_date_str}")
            st.write(f"**Reason:** {description}")
            st.write(f"**Days Remaining:** {days_left}")

            if st.button("↩️ Recall Leave", key=f"recall_{leave_id}"):
                if days_left > 3:
                    recall_reason = "OPERATIONS"
                    update_leave_status(leave_id, "Recalled", reason=recall_reason)
                    st.warning(f"Leave for {employee} has been recalled due to {recall_reason}.")
                    st.rerun()
                else:
                    st.error(f"Cannot recall leave for {employee}. Less than 3 days ({days_left} days) remaining or leave has ended.")

def team_leaves_dashboard_view():
    st.header("Team Leave Dashboard")

    all_employees = ["All Team Members"] + get_all_employees_from_db()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_employee = st.selectbox("Filter by Employee", all_employees)
    with col2:
        selected_status = st.multiselect("Filter by Status", ["Pending", "Approved", "Declined", "Withdrawn", "Recalled"], default=["Pending", "Approved"])
    with col3:
        # Assuming leave types are consistent across the system.
        # For full accuracy, you might fetch distinct leave types from the 'leaves' table.
        all_leave_types = ["Annual", "Sick", "Maternity", "Paternity", "Study", "Compassionate", "Unpaid"]
        selected_leave_type = st.multiselect("Filter by Leave Type", all_leave_types)

    filtered_leaves = get_team_leaves(
        status_filter=selected_status if selected_status else None,
        leave_type_filter=selected_leave_type if selected_leave_type else None,
        employee_filter=selected_employee if selected_employee != "All Team Members" else None
    )

    if not filtered_leaves:
        st.info("No team leaves found matching the selected filters.")
        return

    # Display results in a table for better readability
    st.subheader("Filtered Team Leaves")
    leave_data = []
    for leave in filtered_leaves:
        leave_data.append({
            "Employee": leave["employee_name"],
            "Leave Type": leave["leave_type"],
            "Start Date": leave["start_date"],
            "End Date": leave["end_date"],
            "Status": leave["status"],
            "Description": leave["description"],
            "Decline Reason": leave["decline_reason"] if leave["decline_reason"] else "N/A"
        })

    st.dataframe(leave_data, use_container_width=True)

# Main app structure with tabs for manager
tab1, tab2, tab3 = st.tabs(["Pending Requests", "Approved Leaves (Recall)", "Team Leave Dashboard"])

with tab1:
    pending_leaves_view()

with tab2:
    approved_leaves_for_recall_view()

with tab3:
    team_leaves_dashboard_view()

# Footer (existing)
st.markdown("---")
st.html("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p>Leave Request Management System | Manager View | Built with Streamlit</p>
</div>
""")