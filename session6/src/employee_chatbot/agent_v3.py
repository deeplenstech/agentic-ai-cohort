import os
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from enum import Enum
from crewai.flow.flow import Flow, start, listen, router
from crewai import Agent, Crew, Task, LLM
from .tools import InsertLeaveTool, ReadLeavesTool, GetCurrentDateTool, LeaveType as ToolLeaveType
from crewai_tools import BedrockKBRetrieverTool
from dotenv import load_dotenv
from .utils import bedrock_patches  # noqa: F401

load_dotenv()

# --- Pydantic Models ---

class RequestIntent(str, Enum):
    LEAVE_MANAGEMENT = "leave management"
    POLICY_ACCESS = "policy access"

class LeaveIntent(str, Enum):
    APPLY = "apply"
    FETCH = "fetch"

class LeaveType(str, Enum):
    EARNED_LEAVE = "earned leave"
    SICK_LEAVE = "sick leave"

class LeaveRequest(BaseModel):
    """Specific parameters for leave-related operations."""
    leave_intent: LeaveIntent = Field(..., description="Whether the user wants to apply for leave or fetch their leave history.")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format (required for 'apply' only).")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format (required for 'apply' only).")
    leave_type: Optional[LeaveType] = Field(None, description="Type of leave (required for 'apply' only).")

class PolicyRequest(BaseModel):
    """Specific parameters for policy-related queries."""
    query: str = Field(..., description="The sanitized query for the policy Knowledge Base.")

class RouteResponse(BaseModel):
    """
    Wrapper model for the Router Agent.
    Ensures exclusive routing to either leave management or policy access.
    """
    intent: RequestIntent = Field(None, description="The intent of the request.")
    leave_request: Optional[LeaveRequest] = Field(None, description="Populated if the request is leave-related.")
    policy_request: Optional[PolicyRequest] = Field(None, description="Populated if the request is policy-related.")

# --- Flow State ---

class EmployeeFlowState(BaseModel):
    employee_query: str = ""
    employee_id: str = ""
    conversationHistory: str = ""
    route_data: Optional[RouteResponse] = None
    final_response: str = ""

# --- Flow Implementation ---

class EmployeeChatbotFlow(Flow[EmployeeFlowState]):
    
    @start()
    def classify_and_route(self):
        """First step: Use a Router Agent to classify the intent and extract data."""
        router_agent = Agent(
            role="Query Router",
            goal="Classify user queries into leave management or policy access and extract all relevant parameters into a structured format.",
            backstory=(
                "You are an expert at understanding employee intents. You carefully distinguish between "
                "requests to apply for leave, requests to view leave history, and queries about company policies. "
                "You extract dates and types accurately to ensure downstream agents have clean data."
            ),
            llm=LLM(model=os.environ["MODEL_ID"]),
            tools=[GetCurrentDateTool()]
        )
        
        router_task = Task(
            description=(
                "Analyze the following employee query and classify it. \n"
                "If it is for applying leaves intent will be LEAVE_MANAGEMENT, and leave_intent will be APPLY. You will extract other details like dates and leave type.\n"
                "If it's for fetching leaves, intent will be LEAVE_MANAGEMENT, and leave_intent will be FETCH. No other details will need to be extracted in that case.\n"
                "If it's policy-related in general or even related to leave policy, extract the exact query and intent will be POLICY_ACCESS.\n\n"
                "EMPLOYEE QUERY: {employee_query} \n"
                "CONVERSATION HISTORY: {conversationHistory}"
            ),
            expected_output="A structured RouteResponse object containing the classified intent and extracted parameters.",
            agent=router_agent,
            output_pydantic=RouteResponse
        )
        
        crew = Crew(agents=[router_agent], tasks=[router_task], verbose=True)
        result = crew.kickoff(inputs={
            "employee_query": self.state.employee_query,
            "conversationHistory": self.state.conversationHistory
        })
        
        # print (result.raw)
        self.state.route_data = result.pydantic
        
    @router(classify_and_route)
    def router_logic(self):
        """Decision logic based on the structured output of the Router Agent."""
        if self.state.route_data.intent == RequestIntent.LEAVE_MANAGEMENT:
            return "leave_management"
        elif self.state.route_data.intent == RequestIntent.POLICY_ACCESS:
            return "policy_access"
        return "unsupported"

    @listen("leave_management")
    def handle_leave(self):
        """Specialized agent for leave operations using extracted parameters."""
        leave_req = self.state.route_data.leave_request
        kb_tool = BedrockKBRetrieverTool(knowledge_base_id=os.environ["BEDROCK_KB_ID"])

        leave_agent = Agent(
            role="Leave Manager",
            goal="Execute leave-related operations using the provided parameters and tools.",
            backstory=(
                "You are a specialized HR agent focused only on leave management. You rely on "
                "the parameters provided by the router to execute your tasks accurately."
            ),
            llm=LLM(model=os.environ["MODEL_ID"], temperature=0),
            tools=[InsertLeaveTool(), ReadLeavesTool(), kb_tool]
        )
        
        if leave_req.leave_intent == LeaveIntent.APPLY:
            description = (
                f"Apply for leave for employee {self.state.employee_id}. \n"
                f"Leave Type: {leave_req.leave_type.value if leave_req.leave_type else 'Not specified'} \n"
                f"Start Date: {leave_req.start_date or 'Not specified'} \n"
                f"End Date: {leave_req.end_date or 'Not specified'} \n\n"
                "Check the calendar year, allowed leaves, and current balance before inserting. "
                "If details are missing, politely ask the employee for them."
            )
        else:
            description = (
                f"Fetch and display the leave history for employee {self.state.employee_id}. \n"
                "Use the ReadLeavesTool to provide a clear summary."
            )
            
        task = Task(
            description=description,
            expected_output="A clear, polite response to the employee confirming the action or providing history.",
            agent=leave_agent
        )
        
        crew = Crew(agents=[leave_agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        self.state.final_response = result.raw

    @listen("policy_access")
    def handle_policy(self):
        """Specialized agent for policy queries using the sanitized policy query."""
        policy_req = self.state.route_data.policy_request
        
        kb_tool = BedrockKBRetrieverTool(knowledge_base_id=os.environ["BEDROCK_KB_ID"])
        
        policy_agent = Agent(
            role="Policy Expert",
            goal="Provide accurate information about company policies using the Knowledge Base.",
            backstory=(
                "You are a policy expert. You answer employee questions based strictly on the "
                "official company documentation retrieved from your knowledge base."
            ),
            llm=LLM(model=os.environ["MODEL_ID"], temperature=0),
            tools=[kb_tool]
        )
        
        task = Task(
            description=(
                f"Search the company policy knowledge base for: {policy_req.query} \n\n"
                "Provide a crisp and helpful answer to the employee."
            ),
            expected_output="A concise answer to the policy query.",
            agent=policy_agent
        )
        
        crew = Crew(agents=[policy_agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        self.state.final_response = result.raw

    @listen("unsupported")
    def handle_unsupported(self):
        """Fallback for cases where the router cannot classify the request."""
        self.state.final_response = "I'm sorry, I couldn't understand if you wanted to manage leaves or access policies. Could you please rephrase your request?"
