import os
from crewai import Agent, Crew, Task, LLM
from crewai_tools import BedrockKBRetrieverTool
from . import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import


hr_manager = Agent(
    role="HR Manager",
    goal="Answer the queries from employees on company policies",
    backstory=(
        "You're a seasoned HR Manager. Known to politly reply to queries form the employees "
        "pertaining to the employee policies. You are also known to reply concisely."
    ),
    llm=LLM(model=os.environ["MODEL_ID"]),
    tools=[
        BedrockKBRetrieverTool(
            knowledge_base_id=os.environ["BEDROCK_KB_ID"]
        )
    ]
)

# Use the configuration below instead when reranking is desired in RAG.
#
# Reranking improves retrieval quality by having a second model score each retrieved chunk
# against the query and reorder results by relevance. This means you can cast a wide net
# (numberOfResults: 20) with the initial vector search, then let the reranker surface only
# the most relevant chunks (numberOfRerankedResults: 5) before they reach the LLM — reducing
# token usage and improving answer accuracy.
#
# Amazon Bedrock supports two reranking models (docs: https://docs.aws.amazon.com/bedrock/latest/userguide/rerank-supported.html):
#   - amazon.rerank-v1:0       (not available in us-east-1)
#   - cohere.rerank-v3-5:0     (available in us-east-1, us-west-2, eu-central-1, ap-northeast-1, ca-central-1)
#
# BedrockKBRetrieverTool(
#     knowledge_base_id=os.environ["BEDROCK_KB_ID"],
#     retrieval_configuration={
#         "vectorSearchConfiguration": {
#             "numberOfResults": 20,
#             "rerankingConfiguration": {
#                 "type": "BEDROCK_RERANKING_MODEL",
#                 "bedrockRerankingConfiguration": {
#                     "modelConfiguration": {
#                         "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/cohere.rerank-v3-5:0"
#                     },
#                     "numberOfRerankedResults": 5
#                 }
#             }
#         }
#     }
# )

handbook_query_task = Task(
    description=(
        "Go through the employee handbook to answer employee queries related to the policies.\n"
        "EMPLOYEE_QUERY: {employee_query}\n"
    ),
    expected_output=(
        "A detailed answer to the employee query in plain text. The response should be "
        "empathetic, concise and polite irrespective of the frustration level of the employee"
    ),
    agent=hr_manager
)

crew = Crew(
    agents=[hr_manager],
    tasks=[handbook_query_task],
    verbose=True
)

