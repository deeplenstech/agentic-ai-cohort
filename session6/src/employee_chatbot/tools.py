from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from .utils.session import Session
import os

class LeaveType(str, Enum):
    EARNED_LEAVE = "earned leave"
    SICK_LEAVE = "sick leave"

def _init_db():
    conn = sqlite3.connect("leaves.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            days INTEGER NOT NULL,
            reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

class InsertLeaveInput(BaseModel):
    """Input schema for InsertLeaveTool."""
    employee_id: str = Field(..., description="The ID of the employee requesting leave.")
    leave_type: LeaveType = Field(..., description="The type of leave being requested.")
    start_date: str = Field(..., description="Start date of the leave in YYYY-MM-DD format.")
    end_date: str = Field(..., description="End date of the leave in YYYY-MM-DD format.")
    reason: Optional[str] = Field(None, description="The reason for the leave request.")

class InsertLeaveTool(BaseTool):
    name: str = "Insert requested leaves"
    description: str = "Inserts a requested leave for an employee into the local database. Dates should be in YYYY-MM-DD format."
    args_schema: Type[BaseModel] = InsertLeaveInput

    def _run(self, employee_id: str, leave_type: LeaveType, start_date: str, end_date: str, reason: Optional[str] = None) -> str:
        if (os.getenv("AGENT_VERSION") != "v1" and employee_id != Session().getEmployeeId()):
            raise Exception("Access Denied Error: You can only apply for your own leaves.")
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return "Error: Dates must be in YYYY-MM-DD format."
            
        if start > end:
            return "Error: start_date cannot be after end_date."
            
        days = sum(1 for i in range((end - start).days + 1) if (start + timedelta(days=i)).weekday() < 5)
        
        _init_db()
        conn = sqlite3.connect("leaves.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leaves (employee_id, leave_type, start_date, end_date, days, reason) VALUES (?, ?, ?, ?, ?, ?)",
            (employee_id, leave_type.value, start_date, end_date, days, reason)
        )
        conn.commit()
        conn.close()
        return f"Leave requested successfully for employee {employee_id} ({days} days of {leave_type.value})."

class ReadLeavesInput(BaseModel):
    """Input schema for ReadLeavesTool."""
    employee_id: str = Field(..., description="The ID of the employee to read leaves for.")

class ReadLeavesTool(BaseTool):
    name: str = "Read leaves availed"
    description: str = "Reads the total leaves availed by an employee and recent leaves in the last 12 months."
    args_schema: Type[BaseModel] = ReadLeavesInput

    def _run(self, employee_id: str) -> str:
        if (os.getenv("AGENT_VERSION") != "v1" and employee_id != Session().getEmployeeId()):
            raise Exception("Access Denied Error: You can only access your own leaves")
        _init_db()
        
        twelve_months_ago = (datetime.now() - timedelta(days=366)).strftime("%Y-%m-%d")
        
        conn = sqlite3.connect("leaves.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(days) FROM leaves WHERE employee_id = ?", (employee_id,))
        result = cursor.fetchone()
        total_days = result[0] if result[0] is not None else 0
        
        cursor.execute(
            "SELECT start_date, end_date, leave_type, days, reason FROM leaves WHERE employee_id = ? AND start_date >= ? ORDER BY start_date DESC",
            (employee_id, twelve_months_ago)
        )
        recent_leaves = cursor.fetchall()
        conn.close()
        
        output = f"Total leaves availed by employee {employee_id}: {total_days} days.\n"
        if recent_leaves:
            output += "Leaves taken in the last 12 months:\n"
            for start, end, ltype, days, reason in recent_leaves:
                reason_str = f" (Reason: {reason})" if reason else ""
                output += f"- {ltype}: {start} to {end} ({days} days){reason_str}\n"
        else:
            output += "No leaves taken in the last 12 months.\n"
            
        return output

class GetCurrentDateInput(BaseModel):
    """Input schema for GetCurrentDateTool."""
    pass

class GetCurrentDateTool(BaseTool):
    name: str = "Get current date"
    description: str = "Returns the current date in YYYY-MM-DD format. Use this whenever you need to know today's date."
    args_schema: Type[BaseModel] = GetCurrentDateInput

    def _run(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")