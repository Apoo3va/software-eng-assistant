# AI Software Engineering Assistant

An end to end multi agent system that reads real GitHub issues, investigates bugs, proposes fixes, reviews code, writes and runs tests, generates documentation, and opens real pull requests, all gated behind human approval.

Built as a capstone project demonstrating agentic AI system design: specialized agents, orchestrated handoffs, retrieval augmented generation, long term memory, reflection loops, parallel execution, and real world tool use through the GitHub API.

## Live demo

A live, publicly deployed version of this app is linked in the About section of this repository on GitHub. Open it, enter any public repository owner and name along with a real issue number, and click Run Pipeline to see the full agent chain execute in real time.

## What it does

Given any public GitHub repository and an issue number, the system runs a full software engineering pipeline:

1. Reads and classifies the issue
2. Investigates the likely cause using retrieval over the actual cloned codebase
3. Proposes a code fix grounded in real retrieved code
4. Reviews the fix and sends it back for revision if it is not good enough
5. Writes and runs real automated tests in a sandboxed environment, correcting itself if the tests fail
6. Generates documentation and a changelog entry
7. Pauses for a human to approve or reject the fix
8. On approval, forks the repository, creates a branch, commits the fix, and opens a real pull request

## Agents

| Agent | Responsibility |
|---|---|
| Requirements Analysis | Classifies the issue and extracts acceptance criteria |
| Bug Investigation | Uses retrieval augmented generation over the real codebase to find likely root causes |
| Coding Assistant | Proposes a fix grounded in retrieved code |
| Code Reviewer | Approves or rejects the fix, with a reflection loop back to the Coding Assistant |
| Testing Agent | Writes pytest tests and runs them in a real sandbox, retrying and self correcting on failure |
| Documentation Writer | Generates a changelog entry, code comments, and a readme snippet |

## Architecture

The pipeline is orchestrated with LangGraph as a typed state graph. Every agent reads from and writes to a shared state object, and routing between agents is handled by explicit conditional edges rather than hand written if statements.

Key design points:

* Structured outputs only. Every agent returns strict JSON, validated and repaired automatically if the model returns malformed output.
* Long term memory. Resolved issues are embedded and stored in a vector database, so future runs can recall similar past fixes.
* Retrieval augmented generation. Each target repository is cloned and indexed on demand into its own vector collection, so the Bug Investigation and Coding agents ground their answers in real code rather than guessing.
* Reflection loops. The Code Reviewer can send a rejected fix back to the Coding Assistant, up to a limited number of revisions before escalating to a human. The Testing Agent retries its own test generation when a test fails, feeding the failure back into the next attempt.
* Parallel execution. Once a fix is approved by review, Testing and Documentation run at the same time rather than one after another.
* Human approval gate. Nothing reaches GitHub without an explicit human click.
* Real world action. Approval triggers real API calls: forking the repository if needed, creating a branch, committing the proposed fix, and opening an actual pull request.

## Tech stack

* Python
* LangGraph for orchestration
* Groq API (model openai gpt oss 20b) for the language model calls, chosen for fast inference and a generous free tier
* ChromaDB for the vector store, used for both retrieval augmented generation and long term memory
* Sentence Transformers for local embeddings
* Direct REST calls to the GitHub API for all repository interaction
* pytest, run in a real subprocess sandbox, for test execution
* Streamlit for the web interface and for hosting the live deployment

## Running it locally

Clone the repository and move into the project folder.

Create a virtual environment and activate it.

Install the dependencies listed in requirements.txt using pip.

Create a file literally named dotenv (that is, a file named .env) in the project root containing two values: a Groq API key under the name GROQ_API_KEY, and a GitHub personal access token with repository write access under the name GITHUB_TOKEN.

Start the app with the command streamlit run app.py, then open the local address it prints in your browser.

Enter any public repository owner and name, along with a real issue number from that repository, and click Run Pipeline.

## Human approval and real GitHub automation

When the pipeline finishes, if the fix is flagged as needing review, the interface shows an approval gate. Clicking approve does not just simulate success. It performs real actions against the GitHub API: it forks the target repository into your account if you do not already own it, creates a new branch, commits the proposed fix as a file, and opens an actual pull request that you can open and inspect on GitHub.

This has been tested successfully both against a well known open source project and against a personal repository, where the resulting pull request was reviewed and merged.

## Known limitations

* The free tier of the Groq API imposes rate limits, so heavy repeated use during testing can occasionally trigger a temporary delay.
* Language models occasionally return malformed or empty output. The system includes multiple layers of retry and repair, but this is inherent to working with smaller, free tier models rather than a bug in the pipeline itself.
* Test generation targets illustrative, self contained pytest files rather than tests wired directly into the target repository's own test suite, since the system does not yet install or execute the target project's real dependencies.

## Author

Apoorva Yadav
