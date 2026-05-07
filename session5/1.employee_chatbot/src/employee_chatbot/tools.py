from crewai.tools import tool
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from deepeval.tracing import observe, update_current_span
from deepeval.test_case import LLMTestCase

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
            days INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@tool("Insert requested leaves")
def insert_leave(employee_id: str, leave_type: LeaveType, start_date: str, end_date: str) -> str:
    """
    Inserts a requested leave for an employee into the local database. 
    Dates should be in YYYY-MM-DD format.
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return "Error: Dates must be in YYYY-MM-DD format."
        
    if start > end:
        return "Error: start_date cannot be after end_date."
        
    days = (end - start).days + 1
    
    _init_db()
    conn = sqlite3.connect("leaves.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leaves (employee_id, leave_type, start_date, end_date, days) VALUES (?, ?, ?, ?, ?)",
        (employee_id, leave_type.value, start_date, end_date, days)
    )
    conn.commit()
    conn.close()
    return f"Leave requested successfully for employee {employee_id} ({days} days of {leave_type.value})."

@tool("Read leaves availed")
def read_leaves(employee_id: str) -> str:
    """Reads the total leaves availed by an employee and recent leaves in the last 6 months."""
    _init_db()
    
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    conn = sqlite3.connect("leaves.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(days) FROM leaves WHERE employee_id = ?", (employee_id,))
    result = cursor.fetchone()
    total_days = result[0] if result[0] is not None else 0
    
    cursor.execute(
        "SELECT start_date, end_date, leave_type, days FROM leaves WHERE employee_id = ? AND start_date >= ? ORDER BY start_date DESC",
        (employee_id, six_months_ago)
    )
    recent_leaves = cursor.fetchall()
    conn.close()
    
    output = f"Total leaves availed by employee {employee_id}: {total_days} days.\n"
    if recent_leaves:
        output += "Leaves taken in the last 6 months:\n"
        for start, end, ltype, days in recent_leaves:
            output += f"- {ltype}: {start} to {end} ({days} days)\n"
    else:
        output += "No leaves taken in the last 6 months.\n"
        
    return output

@tool("Get current date")
def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format. Use this whenever you need to know today's date."""
    return datetime.now().strftime("%Y-%m-%d")


# ── DeepEval-observed retriever ───────────────────────────────────────────────
# @observe marks this as a "retriever" span in DeepEval's tracing system.
# During `deepeval test run`, the framework automatically links retrieved chunks
# to the active LLMTestCase as retrieval_context — no manual list passing needed.
#
# Metric choice — ContextualRelevancyMetric:
#   • Evaluates whether the retrieved KB chunks are relevant to the employee's query.
#   • Only requires `input` + `retrieval_context` — no ground-truth `context` needed.
#   • ContextualPrecision/Recall are skipped here because they require a `context`
#     (ground-truth chunks) field that our goldens don't carry.
# from deepeval.metrics import ContextualRelevancyMetric

# _contextual_relevancy = ContextualRelevancyMetric(threshold=0.7)

# @observe(
#     type="retriever",
#     name="Bedrock Knowledge Base",
#     metrics=[_contextual_relevancy],
# )
# def retrieve_from_kb(kb_tool, query: str) -> str:
#     """Call the Bedrock KB tool and register retrieved chunks with DeepEval tracing."""
#     raw_result: str = kb_tool._run(query)
#     chunks = [raw_result]  # BedrockKBRetrieverTool returns a single concatenated string

#     # Register this span's test case — DeepEval evaluates _contextual_relevancy against it
#     update_current_span(
#         test_case=LLMTestCase(
#             input=query,
#             actual_output=raw_result,
#             retrieval_context=chunks,
#         )
#     )
#     return raw_result


# @tool("Retrieve from Knowledge Base")
# def kb_retriever(query: str) -> str:
#     """Retrieves relevant company policy information from the knowledge base."""
#     kb_tool = 
#     raw_result = retrieve_from_kb(kb_tool, query)
#     return raw_result  # return the string back to the agent