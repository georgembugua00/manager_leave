# manager_view.py
import streamlit as st
from datetime import date, timedelta, datetime
from supabase import create_client, Client
import pandas as pd # Still useful for DataFrame conversion

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    """Initialize Supabase client with credentials from Streamlit secrets."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    return supabase



def get_employee_by_name(employee_name):
    """Fetches employee details by name from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("employee_table").select("AUUID, First_Name").eq("First_Name", employee_name).execute()
        if response.data:
            # Supabase returns a list of dictionaries, fetchone equivalent
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error fetching employee by name: {str(e)}")
        return None

def apply_for_leave(employee_id, leave_type, start_date, end_date, description, attachment):
    """Adds a new leave application to the Supabase database."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").insert({
            "employee_id": employee_id,
            "leave_type": leave_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "description": description,
            "attachment": bool(attachment),
            "status": "Pending"
        }).execute()
        if response.data:
            return True, "Leave request submitted successfully!"
        return False, "Failed to submit leave request"
    except Exception as e:
        return False, f"Error submitting leave request: {str(e)}"

def get_leave_history(employee_id):
    """Fetches the leave history for a specific employee from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "leave_type, start_date, end_date, description, status, decline_reason, recall_leave"
        ).eq("employee_id", employee_id).order("start_date", desc=True).execute()

        if response.data:
            # Convert to list of tuples for consistency with original SQLite output format
            history = []
            for row in response.data:
                history.append((
                    row['leave_type'],
                    row['start_date'],
                    row['end_date'],
                    row['description'],
                    row['status'],
                    row.get('decline_reason'),
                    row.get('recall_reason')
                ))
            return history
        return []
    except Exception as e:
        st.error(f"Error fetching leave history: {str(e)}")
        return []

def get_all_pending_leaves():
    """Fetches all leave requests with a 'Pending' status for the manager from Supabase."""
    supabase = init_supabase()
    try:
        # Join leaves with employees to get employee name
        response = supabase.table("off_roll_leave").select(
            "AUUID, employee_id, leave_type, start_date, end_date, description, employee_table(First_Name)"
        ).eq("status", "Pending").execute()

        if response.data:
            pending_leaves = []
            for row in response.data:
                # Extract employee name from the nested 'employees' dictionary
                employee_name = row['employee_table']['First_Name'] if row['employee_table'] else None
                pending_leaves.append({
                    "id": row['employee_id'],
                    "employee_name": employee_name,
                    "leave_type": row['leave_type'],
                    "start_date": row['start_date'],
                    "end_date": row['end_date'],
                    "description": row['description']
                })
            return pending_leaves
        return []
    except Exception as e:
        st.error(f"Error fetching pending leaves: {str(e)}")
        return []

def get_approved_leaves():
    """Fetches all leave requests with an 'Approved' status from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "AUUID, employee_id, leave_type, start_date, end_date, description, employee_table(First_Name)"
        ).eq("status", "Approved").execute()

        if response.data:
            approved_leaves = []
            for row in response.data:
                employee_name = row['employee_table']['First_Name'] if row['employee_table'] else None
                approved_leaves.append({
                    "id": row['AUUID'],
                    "employee_name": employee_name,
                    "leave_type": row['leave_type'],
                    "start_date": row['start_date'],
                    "end_date": row['end_date'],
                    "description": row['description']
                })
            return approved_leaves
        return []
    except Exception as e:
        st.error(f"Error fetching approved leaves: {str(e)}")
        return []

def update_leave_status(employee_id, new_status, reason=None):
    """Updates the status of a leave request in Supabase."""
    supabase = init_supabase()
    update_data = {"status": new_status}
    if new_status == "Declined":
        update_data["decline_reason"] = reason
    elif new_status == "Recalled":
        update_data["recall_reason"] = reason
    elif new_status == "Withdrawn": # Added for consistency with withdraw_leave
        update_data["recall_reason"] = reason

    try:
        response = supabase.table("off_roll_leave").update(update_data).eq("employee_id", employee_id).execute()
        if response.data:
            return True, f"Leave status updated to {new_status}"
        return False, "Failed to update leave status"
    except Exception as e:
        return False, f"Error updating leave status: {str(e)}"

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """Fetches all team leaves with optional filters for the manager's dashboard from Supabase."""
    supabase = init_supabase()
    try:
        query = supabase.table("off_roll_leave").select(
            "employee_id, leave_type, start_date, end_date, status, description, decline_reason, employee_table(First_Name)"
        )

        if status_filter:
            query = query.in_("status", status_filter)
        if leave_type_filter:
            query = query.in_("leave_type", leave_type_filter) # Corrected potential typo: ensure it's not `query = query = query.in_`
        if employee_filter and employee_filter != "All Team Members":
            query = query.eq("employee_table.First_Name", employee_filter)

        response = query.execute()

        if response.data:
            leaves = []
            for row in response.data:
                employee_name = row['employee_table']['First_Name'] if row['employee_table'] else None
                leaves.append({ # <--- THIS IS THE KEY CHANGE! Now creating a dictionary
                    "employee_name": employee_name, # Add the key "employee_name":
                    "leave_type": row['leave_type'],
                    "start_date": row['start_date'],
                    "end_date": row['end_date'],
                    "status": row['status'],
                    "description": row['description'],
                    "decline_reason": row.get('decline_reason')
                })
            return leaves
        return []
    except Exception as e:
        st.error(f"Error fetching team leaves: {str(e)}")
        return []

def get_all_employees_from_db():
    """Gets a unique list of all employees from the employees table in Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("employee_table").select("First_Name").order("First_Name", desc=False).execute()
        if response.data:
            employees = [row['First_Name'] for row in response.data]
            return employees
        return []
    except Exception as e:
        st.error(f"Error fetching employees: {str(e)}")
        return []

def get_all_leaves():
    """Fetches all leave records from Supabase, joining with employee names."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "AUUID, leave_type, start_date, end_date, description, status, employee_table(First_Name)"
        ).execute()

        if response.data:
            leaves = []
            for row in response.data:
                employee_name = row['employee_table']['First Name'] if row['employee_table'] else None
                leaves.append({
                    "id": row["AUUID"],
                    "name": employee_name,
                    "type": row["leave_type"],
                    "start": row["start_date"],
                    "end": row["end_date"],
                    "description": row["description"],
                    "status": row["status"]
                })
            return leaves
        return []
    except Exception as e:
        st.error(f"Error fetching all leaves: {str(e)}")
        return []

def withdraw_leave(leave_id, recall_reason=None):
    """Marks a leave request as Withdrawn in Supabase with an optional reason."""
    # This calls update_leave_status for consistency
    return update_leave_status(employee_id, "Withdrawn", recall_reason)

def get_latest_leave_entry():
    """Fetches the details of the most recently added leave entry from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "leave_type, start_date, end_date, description, status, decline_reason, recall_reason, employee_table(First_Name)"
        ).order("id", desc=True).limit(1).execute()

        if response.data:
            row = response.data[0]
            employee_name = row['employee_table']['First_Name'] if row['employees'] else None
            return {
                "employee_name": employee_name,
                "leave_type": row['leave_type'],
                "start_date": row['start_date'],
                "end_date": row['end_date'],
                "description": row['description'],
                "status": row['status'],
                "decline_reason": row.get('decline_reason'),
                "recall_reason": row.get('recall_reason')
            }
        return None
    except Exception as e:
        st.error(f"Error fetching latest leave entry: {str(e)}")
        return None

def get_employee_leave_entitlements(employee_id):
    """Fetches leave entitlements for a given employee from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("leave_entitlements").select("*").eq("employee_id", employee_id).execute()
        if response.data:
            return response.data[0] # Return the first matching record
        return None
    except Exception as e:
        st.error(f"Error fetching employee leave entitlements: {str(e)}")
        return None

def get_employee_used_leave(employee_id, leave_type=None):
    """Calculates total used leave days for an employee, optionally by type, from Supabase."""
    supabase = init_supabase()
    try:
        query = supabase.table("off_roll_leave").select("start_date, end_date").eq("employee_id", employee_id).eq("status", "Approved")
        if leave_type:
            query = query.eq("leave_type", leave_type)

        response = query.execute()
        used_days = 0
        if response.data:
            for record in response.data:
                start = datetime.fromisoformat(record['start_date'])
                end = datetime.fromisoformat(record['end_date'])
                used_days += (end - start).days + 1 # +1 to include start and end day
        return int(used_days)
    except Exception as e:
        st.error(f"Error calculating used leave: {str(e)}")
        return 0

# Initialize DB (ensure this runs only once per session)
#if 'db_initialized_supabase' not in st.session_state:
#    init_db_supabase()
#    st.session_state['db_initialized_supabase'] = True

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
                if st.button("✅ Approve", key=f"approve_{employee_id}"):
                    update_leave_status(employee_id, "Approved")
                    st.success(f"Leave for {employee} approved.")
                    st.rerun()
            with col2:
                if st.button("❌ Decline", key=f"decline_{employee_id}"):
                    if f"show_reason_{employee_id}" not in st.session_state:
                        st.session_state[f"show_reason_{employee_id}"] = False
                    st.session_state[f"show_reason_{employee_id}"] = not st.session_state[f"show_reason_{employee_id}"]

                    if st.session_state[f"show_reason_{leave_id}"]:
                        decline_reason = st.text_input("Reason for declining:", key=f"reason_{employee_id}")
                        if st.button("Confirm Decline", key=f"confirm_decline_{employee_id}"):
                            if decline_reason:
                                update_leave_status(employee_id, "Declined", reason=decline_reason)
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
