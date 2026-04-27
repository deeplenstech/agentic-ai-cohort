# Assignment 1: AWS Knowledge Base with Vector Store

## Objective

Build, test, and evaluate an AWS Bedrock Knowledge Base backed by a vector store. You will upload a source document to S3, configure semantic chunking and an embedding model, synchronize the knowledge base, test retrieval and generation through the AWS UI, and run a formal evaluation using the provided JSONL dataset.

---

## Source Document

`employee_handbook.pdf` is included in this folder. It serves as the knowledge base source.

> **Note:** This employee handbook was generated with ChatGPT and is intentionally imperfect. It may contain inconsistencies, ambiguities, or errors — which makes it a realistic test of how well your knowledge base handles noisy real-world documents. Keep this in mind when interpreting evaluation scores.

---

## Step 1: Upload the Employee Handbook to S3

1. Open the [AWS S3 Console](https://s3.console.aws.amazon.com/).
2. Create a **new S3 bucket** (e.g., `my-knowledgebase-source-<yourname>`). Use the same AWS region you intend to use for Bedrock (e.g., `us-east-1`).
3. Inside the bucket, create a **new folder** (e.g., `employee-handbook/`).
4. Upload `employee_handbook.pdf` into that folder.

**AWS Docs:** [Creating a bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html) | [Uploading objects](https://docs.aws.amazon.com/AmazonS3/latest/userguide/upload-objects.html)

---

## Step 2: Create the Knowledge Base in AWS Bedrock

Navigate to **AWS Bedrock → Knowledge Bases → Create → Knowledge Base with vector store**. You will configure a knowledge base backed by a new S3 vector store.

### 2a. General Settings

- Give the knowledge base a name (e.g., `employee-policy-kb`).
- Bedrock will auto-create an IAM role for you — leave this as default unless you have a specific role.

**AWS Docs:** [Create a knowledge base](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-create.html)

### 2b. Configure the Data Source

- Select **Amazon S3** as the data source and click on Next.
- Select the S3 bucket you created, then select the specific folder (e.g., `employee-handbook/`) that contains `employee_handbook.pdf`.

### 2c. Parsing Strategy

When configuring the data source, set the parser to **Amazon Bedrock Data Automation**. This parser uses AI to intelligently extract text from PDFs, including complex layouts, tables, and multi-column formats — resulting in cleaner input for chunking and embeddings compared to the default parser.

**AWS Docs:** [Parsing options for knowledge bases](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-advanced-parsing.html)

### 2d. Chunking Strategy — Semantic Chunking

When prompted for chunking strategy, select **Semantic chunking**.

Semantic chunking groups text into chunks based on meaning rather than fixed token counts. Unlike fixed-size chunking (which can split a sentence mid-thought), semantic chunking detects topic boundaries so each chunk is more self-contained and coherent. This leads to higher-quality retrieved passages, especially for HR documents where context often spans multiple sentences.

**AWS Docs:** [Chunking strategies for knowledge bases](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-chunking-parsing.html)

### 2e. Embedding Model

Choose an embedding model from the list. Recommended options available in Bedrock:

| Model | Provider | Notes |
|---|---|---|
| `amazon.titan-embed-text-v2` | Amazon | Good general-purpose baseline |
| `cohere.embed-english-v3` | Cohere | Strong for English HR/policy text |
| `cohere.embed-multilingual-v3` | Cohere | Use if multilingual support is needed |

Select whichever you prefer. The embedding model converts text chunks into vectors for similarity search.

**AWS Docs:** [Supported embedding models](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-supported.html)

### 2f. Vector Store — New S3 Vector Store

For the destination vector store, select **Amazon S3 vectors** (or "New vector store in S3"). This keeps the setup entirely within AWS without requiring an external vector database.

**AWS Docs:** [Vector store options](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-setup-oss.html)

Confirm and create the knowledge base.

---

## Step 3: Synchronize the Data Source

After the knowledge base is created, it will not contain any data until you synchronize.

1. In the knowledge base detail page, go to the **Data source** tab.
2. Select your S3 data source and click **Sync**.
3. Wait for the sync job to complete (status will change to `Available`).

During synchronization, Bedrock reads the PDF, parses it, applies semantic chunking, generates embeddings via your chosen model, and writes the resulting vectors into the S3 vector store.

**AWS Docs:** [Sync your data source](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-ingest.html)

---

## Step 4: Test the Knowledge Base

On the knowledge base detail page, use the **Test Knowledge Base** button on the right.

### Retrieval Only

Switch the mode to **Retrieval only** and enter a query, for example:

> How many casual leave days does DeepLens provide?

You should see ranked text chunks returned from the vector store — these are the raw passages Bedrock retrieved from the handbook.

### Retrieval + Generation

Switch the mode to **Retrieval and response generation**. Select a foundation model (e.g., `Claude 3 Sonnet` or `Claude 3 Haiku`) to generate a grounded answer from the retrieved passages.

This is the full RAG (Retrieval-Augmented Generation) flow. Notice how the answer is grounded in the source document.

**AWS Docs:** [Test a knowledge base](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-test.html)

---

## Step 5: Evaluate the Knowledge Base

### Evaluation Dataset

`eval_data_set.jsonl` in this folder contains **10 question-answer pairs** in the Bedrock evaluation format. Each entry has a question and a reference answer derived from the employee handbook. For example:

```json
{
  "conversationTurns": [{
    "prompt": {"content": [{"text": "How many casual leave days does DeepLens provide?"}]},
    "referenceResponses": [{"content": [{"text": "DeepLens typically provides 8 to 12 casual leave days per year."}]}]
  }]
}
```

### Running the Evaluation

1. In the left navigation pane, under **Assess**, select **Evaluations**.
2. In the **RAG evaluations** pane, choose **Create**.
3. Enter a name for the evaluation job and select an **evaluator model** (e.g., `Claude 3.5 Sonnet` or `Amazon Nova Pro`).
4. Under **Inference source**, choose **Bedrock Knowledge Base** and select the knowledge base you just created.
5. Set **Evaluation type** to **Retrieval and response generation**.
6. Select metrics from the table below.
7. Select the S3 path where you have already uploaded `eval_data_set.jsonl` as the prompt dataset.
8. Specify an S3 location for results, then submit.

**Retrieve-and-generate metrics** (select those relevant to your use case):

| Metric | What it measures |
|---|---|
| **Correctness** | Whether the generated answer is accurate relative to the reference |
| **Completeness** | Whether all aspects of the question are fully addressed |
| **Helpfulness** | Overall usefulness of the response |
| **Faithfulness** | Whether the answer is grounded in retrieved passages (no hallucinations) |
| **Logical Coherence** | Whether the response is free from logical gaps or contradictions |
| **Citation Precision** | Whether cited passages are correctly cited |
| **Citation Coverage** | Whether the response is fully supported by the cited passages |

9. Wait for the job to complete. Results will show per-metric scores.

**AWS Docs:** [Knowledge base evaluation](https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation-kb.html) | [Evaluation metrics](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-evaluation-metrics.html) | [Creating a RAG evaluation job](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-evaluation-create-randg.html)

### Interpreting and Improving Scores

If scores are low, consider these adjustments:

- **Low faithfulness** → The model is hallucinating beyond what was retrieved. Try a more instruction-following model or add a system prompt that restricts it to the retrieved context.
- **Low correctness/completeness** → The handbook text itself may be ambiguous (recall it was ChatGPT-generated). You can add a custom prompt or update the source document and re-sync.

After making changes, re-sync the data source and re-run the evaluation to compare.

---

## Summary Checklist

- [ ] Upload `employee_handbook.pdf` to a new S3 bucket
- [ ] Create AWS Bedrock Knowledge Base with S3 as data source
- [ ] Configure **semantic chunking**
- [ ] Choose an **embedding model** (Titan or Cohere)
- [ ] Set destination to a **new S3 vector store**
- [ ] **Synchronize** the data source and wait for completion
- [ ] **Test retrieval** from the knowledge base UI
- [ ] **Test retrieval + generation** with a foundation model
- [ ] Run a **Bedrock evaluation job** using `eval_data_set.jsonl`
- [ ] Enable both retrieval and generation metrics
- [ ] Review scores and iterate on the knowledge base if needed
