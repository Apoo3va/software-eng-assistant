# AI Software Engineering Assistant

An end to end multi agent system that reads real GitHub issues, investigates bugs, proposes fixes, reviews code, writes and runs tests, generates documentation, and opens real pull requests, all gated behind human approval.

This was built as a capstone project to demonstrate practical, production style agentic AI system design rather than a toy demo: specialized agents with clear responsibilities, orchestrated handoffs, retrieval augmented generation grounded in real code, long term memory, reflection loops, parallel execution, structured outputs, graceful error handling, and genuine real world tool use through the GitHub API, including opening and merging real pull requests.

## Live demo

A live, publicly deployed version of this app is linked in the About section of this repository on GitHub. Open it, enter any public repository owner and name along with a real issue number from that repository, and click Run Pipeline to watch the full agent chain execute in real time.

## What it does

Given any public GitHub repository and an issue number, the system runs a complete, six stage software engineering pipeline.

1. Requirements Analysis reads the raw issue text and turns it into structured data: whether it is a bug, a feature, or a chore, a one sentence summary, a list of acceptance criteria, and an estimated complexity.
2. If the issue is a bug, Bug Investigation clones and indexes the target repository into a local vector database, then retrieves the most relevant real code chunks and uses them to reason about likely root causes and suspected files, rather than guessing.
3. Coding Assistant proposes an actual code fix, again grounded in the retrieved code, along with a risk level and a flag for whether a human should review it.
4. Code Reviewer evaluates the proposed fix. If it is rejected, the system automatically sends it back to the Coding Assistant for another attempt, up to a limited number of revisions, after which it escalates to a human rather than looping forever.
5. Once review passes, Testing Agent and Documentation Writer run at the same time. The Testing Agent writes a real, self contained pytest file and actually executes it in a sandboxed subprocess. If the tests fail because of a mistake in the generated test code itself, it feeds that failure back into a second attempt automatically. The Documentation Writer produces a changelog entry, inline code comments, and a short readme style snippet describing the change.
6. The pipeline pauses and shows a human approval gate in the interface. Nothing happens automatically past this point.
7. When a human clicks approve, the system performs real GitHub actions: it forks the target repository into the user's account if they do not already own it, creates a new branch, commits the proposed fix as a file, and opens an actual pull request with a full description, linking back to the original issue.

Every resolved issue that gets approved is also stored in a long term memory collection, so future runs on similar issues can recall and reference what was done before.

## Agents

| Agent | File | Responsibility |
|---|---|---|
| Requirements Analysis | agent requirements.py | Fetches the GitHub issue and classifies it into structured JSON |
| Bug Investigation | agent bug investigation.py | Uses retrieval augmented generation over the real, cloned codebase to identify likely root causes and files |
| Coding Assistant | agent coding.py | Proposes a fix grounded in retrieved code |
| Code Reviewer | agent code review.py | Approves or rejects the fix and provides feedback, with a reflection loop back to the Coding Assistant |
| Testing Agent | agent testing.py | Writes pytest tests and runs them in a real sandbox, retrying and correcting itself when a test fails due to a mistake in the generated test |
| Documentation Writer | agent documentation.py | Generates a changelog entry, code comments, and a readme snippet |

## Architecture

The pipeline is orchestrated with LangGraph as a typed state graph, defined in graph.py. Every agent is a node that reads from and writes to one shared, typed state object, defined in graph state.py. Routing between agents is handled through explicit conditional edges rather than nested if statements, which keeps the control flow readable even as more agents and branches are added.

Several design decisions are worth calling out specifically, since they were deliberate engineering choices rather than defaults.

Structured outputs only. Every single agent is required to return strict JSON matching an explicit schema described in its prompt. Since language models occasionally return malformed JSON, especially smaller free tier models, a shared helper in llm utils.py called safe json parse attempts several layers of automatic repair: stripping markdown fences, removing trailing commas, fixing invalid backslash escapes that commonly appear in generated code snippets, and finally asking the model itself to repair its own broken output. A second helper, call llm for json, wraps the entire API call and automatically retries from scratch if the model returns a genuinely empty response, which was traced back to gpt oss models spending their token budget on hidden reasoning before ever writing an answer. Setting reasoning effort to low on every call fixed this at the source.

Long term memory. Approved fixes are embedded and stored in a persistent ChromaDB collection through memory store.py. Before investigating a new bug, the system searches this memory for similar past resolved issues and includes them as context, so the assistant genuinely gets more informed over time rather than starting from zero on every run.

Retrieval augmented generation, built dynamically per repository. Rather than being hard coded to one demo codebase, rag indexer.py clones and indexes whichever repository is entered in the interface, on demand, into its own separate ChromaDB collection keyed by owner and repository name. The first run against a new repository takes longer because of the clone and embedding step, and every run after that reuses the cached index. This means the tool genuinely generalizes to any public repository, not just the one it was originally tested against.

Reflection loops. Two separate reflection mechanisms exist in this system. The Code Reviewer can reject a fix and send it back to the Coding Assistant, up to a limited number of revisions, after which the orchestrator escalates to a human instead of looping indefinitely. Separately, the Testing Agent has its own inner reflection loop: if the tests it writes fail to even run correctly because of a bug in the generated test code itself, the failure output is fed back into a second generation attempt.

Parallel execution. Once a fix clears review, Testing and Documentation Writer both run from the same point in the graph rather than one waiting for the other, since neither depends on the other's output.

Human approval gate. The interface shows a clear approval step and takes no destructive or external action until a person explicitly clicks approve.

Real world action, not simulation. Approval triggers github actions.py, which performs genuine GitHub API calls: forking the repository if needed, creating a branch, committing the actual proposed fix as a file, and opening a real pull request with a full, linked description. This has been verified end to end multiple times, including against a well known open source project and against a personal repository, where the resulting pull request was reviewed and merged for real.

Defensive error handling throughout. Every agent node applies sensible default values if the model omits an expected field, network and rate limit errors are caught and surfaced clearly in the interface instead of crashing silently, and the Streamlit app disables the run button while a pipeline is already executing to prevent overlapping runs from exhausting the API rate limit.

## Tech stack

* Python
* LangGraph for multi agent orchestration and state management
* Groq API, using the openai gpt oss 20b model, chosen specifically for its fast inference speed and generous free tier limits after an earlier model this project relied on was deprecated mid development
* ChromaDB as the vector store, used both for retrieval augmented generation over target codebases and for long term memory of resolved issues
* Sentence Transformers, specifically the all MiniLM L6 v2 model, for local embeddings, so no external embedding API or cost is required
* Direct REST calls to the GitHub API using the requests library, for fetching issues and for all repository automation
* pytest, executed in a real subprocess sandbox, for actual test generation and execution
* Streamlit for the web interface, and for hosting the free, public deployment

## Project structure

* app.py, the Streamlit interface
* graph.py and graph state.py, the LangGraph orchestration layer and shared state definition
* agent requirements.py, agent bug investigation.py, agent coding.py, agent code review.py, agent testing.py, agent documentation.py, the six specialized agents
* rag indexer.py and rag retriever.py, dynamic per repository retrieval augmented generation
* memory store.py, long term memory of resolved issues
* llm utils.py, shared, resilient JSON parsing and LLM calling helpers used by every agent
* github actions.py, real GitHub automation: forking, branching, committing, and opening pull requests

## Running it locally

Clone the repository and move into the project folder.

Create a virtual environment and activate it.

Install the dependencies listed in requirements.txt using pip.

Create a file literally named dotenv, that is a file named .env, in the project root containing two values: a Groq API key under the name GROQ underscore API underscore KEY, and a GitHub personal access token with repository write access under the name GITHUB underscore TOKEN.

Start the app with the command streamlit run app.py, then open the local address it prints in your browser.

Enter any public repository owner and name, along with a real issue number from that repository, and click Run Pipeline.

## Known limitations

* The free tier of the Groq API imposes both daily and per minute token limits, so heavy repeated use during testing can occasionally trigger a temporary rate limit delay. The interface surfaces this clearly rather than crashing.
* Language models occasionally return malformed or genuinely empty output, particularly smaller free tier models under load. The system includes multiple layers of retry and repair for this, but it is an inherent characteristic of working with free tier models rather than a defect in the pipeline logic itself.
* Generated tests are self contained, illustrative pytest files rather than tests wired directly into the target repository's own existing test suite and dependencies, since the system does not install or execute the target project's real environment.

## Author

Apoorva Yadav
