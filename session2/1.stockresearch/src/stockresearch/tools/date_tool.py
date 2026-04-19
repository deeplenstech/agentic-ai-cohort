from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel
from datetime import date


class GetCurrentDateInput(BaseModel):
    """Input schema for GetCurrentDateTool."""

class GetCurrentDateTool(BaseTool):
    name: str = "get_current_date"
    description: str = "Returns today's date in yyyy-mm-dd format."
    args_schema: Type[BaseModel] = GetCurrentDateInput

    def _run(self) -> str:
        return date.today().isoformat()
