import asyncio
from typing import Optional

from pydantic import BaseModel, Field

from crewai import Agent, Crew, Process, Task
from crewai.flow.flow import Flow, listen, router, start, or_

from deepresearch.crew import deep_research_planner, researcher_agent, writer_agent, critic_agent

# ── Enums & State ───────────────────────────────────────────────────────────────

class SubQuestions(BaseModel):
    sub_questions: Optional[list[str]] = Field(default=None, description="Generated list of research sub questions")

class DeepResearchState(BaseModel):
    # Caller-supplied inputs
    user_query: Optional[str] = Field(default=None, description="Research topic")

    # Internal pipeline state
    sub_questions: Optional[SubQuestions] = Field(default=None, description="Generated research sub questions")
    sub_question_findings: Optional[str] = Field(default="", description="Multiple findings for each sub-question")
    article_draft: Optional[str] = Field(default=None, description="First draft article")
    critic_feedback: Optional[str] = Field(default=None, description="Critic's feedback on draft")

# ── Flow ────────────────────────────────────────────────────────────────────────

class DeepResearchFlow(Flow[DeepResearchState]):

    # ── First pass ───────────────────────────────────────────────────────────────

    @start()
    async def initialize(self):
        pass

    @listen("initialize")
    async def plan(self):
        await self._plan()

    @listen("plan")
    async def runResearch(self):
        await self._research()

    @listen("runResearch")
    async def writeArticle(self):
        await self._write()

    @listen("writeArticle")
    async def critiqueArticle(self):
        await self._critique()

    @router(critiqueArticle)
    def routeAfterCritique(self):
        if not self.state.critic_feedback:
            return "Approved"
        return "NeedsRevision"

    # ── Revision pass ────────────────────────────────────────────────────────────
    @listen("NeedsRevision")
    async def revise(self):
        self.state.sub_question_findings = ""
        self.state.article_draft = ""
        await self._plan()
        await self._research()
        await self._write()

    @listen(or_("Approved", "revise"))
    async def returnArticle(self):
        return self.state.article_draft

    # ── Shared step helpers ──────────────────────────────────────────────────────

    async def _plan(self):
        agent = deep_research_planner.model_copy()
        task = Task(
            description=(
                "USER_QUESTION: {question}\n"
                "CRITIC_FEEDBACK: {critic_feedback}\n"
                "Analyse the user question and decompose it into 2 precise, non-overlapping sub-questions "
                "that together provide comprehensive coverage of the topic. Take critic feedback (if any) "
                "from the previous run into consideration."
            ),
            expected_output="Sub-questions as array in the SubQuestions model",
            output_pydantic=SubQuestions,
            agent=agent
        )
        result = await self._run_crew(
            crew_name="planner",
            inputs={
                "question": self.state.user_query,
                "critic_feedback": self.state.critic_feedback or "None",
            },
            agent=agent,
            task=task
        )
        self.state.sub_questions = result.pydantic

    async def _research(self):
        self.state.sub_question_findings = ""

        async def research_one(sub_question: str):
            agent = researcher_agent.model_copy()
            task = Task(
                description=(
                    "USER_QUESTION: {question}\n"
                    "USER_SUB_QUESTION: {sub_question}\n"
                    "CRITIC_FEEDBACK: {critic_feedback}\n"
                    "Work through sub-question and search for relevant sources, extract detailed "
                    "content from the most promising URLs, and compile a comprehensive findings "
                    "summary with inline [Source: URL] citations. Take critic feedback (if any) "
                    "from the previous run into consideration. Do NOT rely on prior knowledge "
                    "— every fact must come from a retrieved source. Output a findings summary."
                ),
                expected_output=(
                    "Readable string representing the research output containing research "
                    "with inline citations mentioning source urls in [Source: URL] format"
                ),
                agent=agent
            )
            result = await self._run_crew(
                crew_name="researcher",
                inputs={
                    "question": self.state.user_query,
                    "sub_question": sub_question,
                    "critic_feedback": self.state.critic_feedback or "None",
                },
                agent=agent,
                task=task
            )
            self.state.sub_question_findings += result.raw

        coroutines = [research_one(sq) for sq in self.state.sub_questions.sub_questions]
        await asyncio.gather(*coroutines)

    async def _write(self):
        agent = writer_agent.model_copy()
        task = Task(
            description=(
                "USER_QUESTION: {question}\n"
                "USER_SUB_QUESTIONS: {sub_questions}\n"
                "CRITIC_FEEDBACK: {critic_feedback}\n"
                "RESEARCH_FINDINGS: {research_findings}\n"
                "Using the sub-questions and the research findings write a comprehensive "
                "1500-3000 word research article in markdown format. Structure it with a "
                "compelling introduction, body sections aligned to each sub-question, "
                "inline [Source: URL] citations for every factual claim, and a concise conclusion. "
                "Take critic feedback (if any) from the previous run into consideration. "
                "Do NOT invent facts — every claim must be grounded in the research findings."
            ),
            expected_output=(
                "Final research article in markdown format with inline citations "
                "mentioning source urls in [Source: URL] format"
            ),
            agent=agent
        )
        result = await self._run_crew(
            crew_name="writer",
            inputs={
                "question": self.state.user_query,
                "sub_questions": "\n".join(f"Sub-Question {i+1}: {q}" for i, q in enumerate(self.state.sub_questions.sub_questions)),
                "critic_feedback": self.state.critic_feedback or "None",
                "research_findings": self.state.sub_question_findings
            },
            agent=agent,
            task=task
        )
        self.state.article_draft = result.raw

    async def _critique(self):
        agent = critic_agent.model_copy()
        task = Task(
            description=(
                "USER_QUESTION: {question}\n"
                "USER_SUB_QUESTIONS: {sub_questions}\n"
                "ARTICLE_DRAFT: {article_draft}\n"
                "Critically review the article for: factual support and citation completeness, "
                "structural quality and logical coherence, coverage of all sub-questions, and "
                "writing clarity. If the article meets high publication standards, output a blank "
                "string. If the article needs improvement, list specific actionable feedback "
                "referencing exact sentences or sections."
            ),
            expected_output=(
                "Feedback to improve the article in plain text. If no feedback, return a blank string"
            ),
            agent=agent
        )
        result = await self._run_crew(
            crew_name="critic",
            inputs={
                "question": self.state.user_query,
                "sub_questions": "\n".join(f"Sub-Question {i+1}: {q}" for i, q in enumerate(self.state.sub_questions.sub_questions)),
                "article_draft": self.state.article_draft
            },
            agent=agent,
            task=task
        )
        self.state.critic_feedback = result.raw.strip()

    # ── Helpers ──────────────────────────────────────────────────────────────────

    async def _run_crew(self, crew_name: str, agent: Agent, task: Task, inputs: dict):
        crew = Crew(
            name=f"{crew_name}_crew",
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        result = await crew.kickoff_async(inputs=inputs)
        return result
