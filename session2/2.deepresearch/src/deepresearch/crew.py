import os
from crewai import Agent, Crew, Task, LLM, Process
from crewai.agents.crew_agent_executor import CrewAgentExecutor
from crewai.llms.providers.bedrock.completion import BedrockCompletion
from pydantic import BaseModel, Field
from crewai_tools import TavilySearchTool, TavilyExtractorTool

# Some Bedrock-hosted models reject the stopSequences field.
# Patch _get_inference_config to strip it out before the boto3 converse call.
_orig_get_inference_config = BedrockCompletion._get_inference_config

def _get_inference_config_no_stop(self):
    config = _orig_get_inference_config(self)
    config.pop("stopSequences", None)
    return config

BedrockCompletion._get_inference_config = _get_inference_config_no_stop

# CrewAI 1.14.x bug: _parse_native_tool_call uses `func_info.get("arguments", "{}")`
# which defaults to the non-empty string "{}" when the Bedrock response has no
# "function" wrapper. That truthy default short-circuits the `or` so the actual
# `input` dict from the Bedrock toolUse block is never read → empty args {} → validation error.
#
# Bedrock/Claude-Sonnet-4.6 secondary bug: when the "function" wrapper IS present,
# Bedrock serializes the name and arguments with extra wrapping single-quotes, e.g.:
#   "name": "'tavily_search'"  →  should be  "name": "tavily_search"
#   "arguments": "'{\"q\": 1}'"  →  should be  "arguments": "{\"q\": 1}"
# This makes tool-name lookup fail and JSON argument parsing fail.
# The fix below strips those spurious quotes before delegating to the original parser.
_orig_parse = CrewAgentExecutor._parse_native_tool_call

def _strip_bedrock_quotes(value: str) -> str:
    """Strip a single layer of wrapping single-quotes added by Bedrock serialization."""
    if isinstance(value, str) and len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        return value[1:-1]
    return value

def _parse_native_tool_call_fixed(self, tool_call):
    if isinstance(tool_call, dict):
        # Case 1 — raw Bedrock toolUse block (no "function" wrapper)
        if "input" in tool_call and "function" not in tool_call:
            from crewai.utilities.agent_utils import sanitize_tool_name
            call_id = (
                tool_call.get("id")
                or tool_call.get("toolUseId")
                or f"call_{id(tool_call)}"
            )
            func_name = sanitize_tool_name(tool_call.get("name", ""))
            func_args = tool_call.get("input", {})
            return call_id, func_name, func_args

        # Case 2 — "function" wrapper present but name/arguments wrapped in extra single-quotes
        if "function" in tool_call:
            func = tool_call["function"]
            if isinstance(func, dict):
                if isinstance(func.get("name"), str):
                    func["name"] = _strip_bedrock_quotes(func["name"])
                if isinstance(func.get("arguments"), str):
                    func["arguments"] = _strip_bedrock_quotes(func["arguments"])

    return _orig_parse(self, tool_call)

CrewAgentExecutor._parse_native_tool_call = _parse_native_tool_call_fixed

deep_research_planner = Agent(
    role="Deep Research Planner",
    goal=(
        "Decompose a broad research question into 2 precise, non-overlapping sub-question "
        "that together provide comprehensive coverage of the question."
    ),
    backstory=(
        "You are an expert research strategist with a background in academic literature review "
        "and investigative journalism. You excel at identifying the key dimensions of a complex "
        "question and formulating targeted questions that will yield actionable insights when "
        "answered independently and then synthesized. You think like an editor commissioning "
        "a cover story: what are the essential angles a reader needs to understand the full picture? "
    ),
    llm=LLM(model=os.environ["LARGE_MODEL_ID"]),
    tools=[TavilySearchTool()]
)

researcher_agent = Agent(
    role="Deep Research Investigator",
    goal=(
        "Research a specific research sub-question thoroughly using web search and URL content extraction. "
        "Produce a comprehensive findings summary with full source citations. "
        "It is important that you don't rely on your knowledge, rather rely on information searched "
        "and extracted from the internet. "
        "When extracting URL content, limit extraction to the top one most relevant URL per sub-question — "
        "do not extract content from every search result. "
    ),
    backstory=(
        "You are a skilled investigative researcher who gathers primary source evidence using "
        "web search and content extraction. You are meticulous about citing sources — for every claim "
        "you make, you record the source URL, the exact excerpt that supports the claim. "
        "You never rely on prior knowledge: every fact must be grounded in a source retrieved "
        "during this session. You prioritize authoritative sources such as academic papers, "
        "peer-reviewed journals, government reports, and reputable industry publications. "
    ),
    llm=LLM(model=os.environ["LARGE_MODEL_ID"]),
    tools=[TavilySearchTool(), TavilyExtractorTool()]
)

writer_agent = Agent(
    role="Research Article Writer",
    goal=(
        "Write a structured, authoritative 1000-1500 word research article based on the provided "
        "research and synthesizing findings into a cohesive narrative with proper inline citations. "
    ),
    backstory=(
        "You are a professional science and technology writer with experience writing for "
        "publications like MIT Technology Review and Wired. You write in clear, precise prose, "
        "cite every factual claim with its source URL in the format [Source: URL], and structure "
        "articles with a compelling introduction, logically ordered body sections aligned to the "
        "research plan, and a concise conclusion. You never invent facts — everything you write "
        "is grounded in sources retrieved from the knowledge base. When critic feedback is "
        "provided, you address every point specifically and improve the article accordingly. "
    ),
    llm=LLM(model=os.environ["LARGE_MODEL_ID"])
)

critic_agent = Agent(
    role="Research Article Critic",
    goal=(
        "Review a research article draft for factual support, structural quality, citation "
        "completeness, and logical coherence. Produce a structured critique with specific "
        "actionable revision instructions, or output APPROVED if ready for publication. "
    ),
    backstory=(
        "You are a rigorous peer reviewer and editorial standards enforcer with experience "
        "in academic publishing and long-form journalism. You identify unsupported claims, "
        "structural weaknesses, missing perspectives, and citation gaps. Your critiques are "
        "specific and constructive: you flag exact sentences or sections that need revision "
        "and explain precisely how to fix them. You understand that the article should cite "
        "every factual claim with [Source: URL] format. You output blank string only when the "
        "article meets high publication standards. "
    ),
    llm=LLM(model=os.environ["LARGE_MODEL_ID"]),
    tools=[TavilySearchTool()]
)

manager_agent = Agent(
    role="Deep Research Manager",
    goal=(
        "Orchestrate the full deep research workflow by delegating each step to the right specialist: "
        "planning to the Research Planner, investigation to the Research Investigator, "
        "writing to the Article Writer, and critique to the Article Critic. "
        "Ensure each step completes fully before the next begins, and drive the feedback loop "
        "if the critic requests revisions."
    ),
    backstory=(
        "You are a senior research director who has led large investigative teams at top-tier "
        "publications. You do not do the research yourself — you assign the right work to the "
        "right specialist, review their outputs for completeness, and coordinate handoffs between "
        "planning, investigation, writing, and editorial review. "
        "You are decisive and keep the team focused: you never allow a step to be skipped and "
        "you ensure the critic's feedback is fully acted on before the final article is delivered."
    ),
    llm=LLM(model=os.environ["LARGE_MODEL_ID"]),
    allow_delegation=True
)

research_task = Task(
    description=(
        "USER QUERY: {user_query}\n\n"
        "Execute the following steps in order:\n\n"
        "Step 1 — Research Planning\n"
        "Analyse the user query and decompose it into 2 precise, non-overlapping sub-questions "
        "that together provide comprehensive coverage of the topic. "
        "Output the numbered list of sub-questions before proceeding.\n\n"
        "Step 2 — Sub-Question Investigation\n"
        "Work through each sub-question from Step 1 ONE AT A TIME. For each sub-question: "
        "search for relevant sources, extract detailed content from the most promising URLs, "
        "and compile a comprehensive findings summary with inline [Source: URL] citations. "
        "Finish all research for one sub-question before moving to the next. "
        "Do NOT rely on prior knowledge — every fact must come from a retrieved source. "
        "Output a findings summary for each sub-question before proceeding.\n\n"
        "Step 3 — Article Writing\n"
        "Using the sub-questions from Step 1 and the findings from Step 2, write a comprehensive "
        "1500-3000 word research article in markdown format. Structure it with a compelling "
        "introduction, body sections aligned to each sub-question, inline [Source: URL] citations "
        "for every factual claim, and a concise conclusion. "
        "Do NOT invent facts — every claim must be grounded in the Step 2 findings.\n\n"
        "Step 4 — Critical Review (performed only once)\n"
        "Critically review the article written in Step 3 for: factual support and citation "
        "completeness, structural quality and logical coherence, coverage of all sub-questions, "
        "and writing clarity.\n"
        "  - If the article meets high publication standards, output the final markdown article "
        "followed by the word APPROVED. You are done.\n"
        "  - If the article needs improvement, list specific actionable feedback referencing exact "
        "sentences or sections. Then immediately loop back to Step 1 — incorporate the feedback "
        "into a revised research plan, re-execute Step 2 (re-investigate as needed) and Step 3 "
        "(rewrite the article). After producing the revised article, output it as your final answer. "
        "Do NOT run Step 4 again — the critical review happens only once."
    ),
    expected_output=(
        "A complete research article in markdown format (1000-1500 words) with proper headings "
        "and inline [Source: URL] citations, followed by either 'APPROVED' or a structured "
        "critique with specific revision instructions."
    )
)

crew = Crew(
    agents=[deep_research_planner, researcher_agent, writer_agent, critic_agent],
    tasks=[research_task],
    process=Process.hierarchical,
    manager_agent=manager_agent,
    verbose=True
)
