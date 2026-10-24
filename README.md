# Reboot AI

**Give forgotten projects a second wind.**

Reboot AI helps developers return to unfinished or abandoned code
projects without spending hours reconstructing what they were building.
Point it at a local Git repository and it builds a project report,
searches arXiv for potentially relevant research, and uses the
repository evidence and retrieved papers to suggest a practical restart
plan.

> **Project status:** Early-stage prototype. Research matches and
> AI-generated recommendations are leads to verify, not guaranteed
> fixes.

## Why Reboot?

Returning to an old repository often means rereading the README,
scanning files and commit history, hunting for TODOs, and trying to
remember which ideas were worth pursuing. Reboot brings these clues
together in one report and suggests concrete next steps.

The goal is not to write the entire project for you. It is to reduce the
friction of getting started again.

## What it does

-   **Inspects a local repository:** gathers the README, file inventory,
    recent commits, working-tree status, TODO/FIXME markers, and
    selected source-file excerpts.
-   **Summarizes the project:** identifies apparent purpose, implemented
    features, missing pieces, and possible architectural limitations.
-   **Finds research leads:** derives search queries from repository
    evidence, searches arXiv, deduplicates and ranks candidate papers,
    and attempts limited PDF text extraction for selected results.
-   **Connects research to code:** uses the configured Gemma model to
    relate repository evidence to retrieved papers and suggest files,
    functions, tests, and next steps.
-   **Provides a fallback:** if AI synthesis is unavailable, Reboot can
    still return repository evidence and retrieved-paper information.

Research retrieval is an internal part of project revival; Reboot is not
intended to be another standalone arXiv search interface.

## How it works

1.  Enter the path to a local Git repository in the web interface.
2.  Reboot inspects the repository and collects available evidence.
3.  It derives a small set of research queries from the README,
    filenames, TODOs, and selected source excerpts.
4.  It searches arXiv, ranks candidate papers, and attempts to extract
    limited text from the highest-ranked PDFs.
5.  The configured Gemma model uses repository evidence and retrieved
    research to draft a restart report.
6.  Review the recommendations, open the original papers, and verify
    their assumptions before implementing anything.

The agent prompt instructs the model to distinguish observations from
inferences, avoid inventing papers or results, and disclose when only an
abstract or excerpt was available. Nevertheless, AI-generated analysis
can be wrong and should be checked.

## Model

Reboot currently uses Google's GenAI SDK to call the Gemma model
configured in `reboot/agent.py`:

``` python
MODEL_NAME = "gemma-4-26b-a4b-it"
```

The API connection has been tested successfully with a direct generation
request. The complete repository-to-restart-plan workflow should also be
tested with this model before considering the integration fully
verified.

Gemma is an open-weight model, but in this setup inference is performed
through Google's hosted API rather than locally on the user's machine. A
Google API key and internet access are required.

## Quickstart

### Requirements

-   Python 3.10 or newer recommended.
-   Git.
-   A Google GenAI API key with access to the configured Gemma model.
-   Internet access for hosted model calls, arXiv searches, and PDF
    retrieval.

### 1. Get the project

Clone the Reboot AI repository using its actual Git URL, or open the
local project directory.

``` bash
git clone <your-repository-url>
cd reboot-ai
```

Replace `<your-repository-url>` with the repository's real URL.

### 2. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
python -m pip install -r requirements.txt
```

### 4. Configure the API key

Create a `.env` file in the project root:

``` dotenv
GEMINI_API_KEY=your_api_key_here
```

Keep `.env` private and never commit API keys. The `.env.example` file
should contain placeholders only.

### 5. Start Reboot

``` bash
python app.py
```

Open the local address printed by Flask in your terminal (typically
`http://127.0.0.1:5000`). Enter the path to a local Git repository and
run the inspection.

Example Windows path:

``` text
D:\Projects\my-forgotten-project
```

Use only repositories you trust and are authorized to inspect.

## Running tests

Run the automated research tests from the project root:

``` bash
python -m unittest discover -s tests -v
```

The existing research tests cover paper relevance ranking, deduplication
and query tracking, and graceful handling of PDF extraction failures.
They do not replace end-to-end testing of the Flask interface, Gemma
synthesis, or a real repository.

## Project structure

``` text
reboot-ai/
├── app.py                  # Flask application and routes
├── reboot/
│   ├── workspace.py        # Local repository inspection
│   ├── agent.py            # Research ranking and restart-plan synthesis
│   └── arxiv_search.py     # arXiv search and limited PDF extraction
├── templates/
│   └── index.html          # Web interface
├── static/
│   └── style.css           # UI styling
├── tests/
│   └── test_research.py    # Research-pipeline tests
├── .env.example            # Placeholder environment configuration
├── .gitignore
└── requirements.txt
```

This is an illustrative overview; filenames may change as development
continues.

## Research and evidence

Reboot uses arXiv search results for paper metadata and abstracts. For a
limited number of high-ranked candidates, it attempts to extract text
from the opening pages of their PDFs. Extraction may fail, and an
excerpt is not equivalent to reading or validating the entire paper.

Open the original paper and check whether its assumptions, methods, and
results apply to your project before acting on a recommendation.
Reboot's relevance ranking is heuristic and does not establish
scientific quality or correctness.

## Privacy and security

Reboot reads files from the repository path you provide. The inspection
is intended to exclude common generated directories and sensitive files,
but you should review the inspected content and the repository before
using the tool.

**Repository content may be sent to the configured hosted model
provider.** This can include the README, file paths, recent Git
metadata, TODO markers, selected source excerpts, research queries, and
retrieved paper excerpts. Do not use Reboot on a private or sensitive
repository unless you are comfortable with that data flow and the
provider's terms.

-   Never put credentials or API keys in your repository.
-   Keep `.env` out of version control.
-   Use only repositories you are authorized to access.
-   Treat generated recommendations as untrusted until verified.
-   Review any suggested code or commands before executing them.

## Current limitations

-   Reboot is an early-stage prototype; broader error handling and
    end-to-end coverage are still needed.
-   Research queries are derived from repository text and topic
    triggers, so relevant work may be missed.
-   Paper ranking is heuristic.
-   PDF extraction is limited and may fail.
-   Model availability, API limits, network access, and output quality
    affect results.
-   A restart plan is advisory; Reboot does not automatically implement
    its suggestions.
-   The direct Gemma API call has succeeded, but the full restart-plan
    workflow still needs verification with Gemma.

## Roadmap

-   [x] Inspect local repository evidence and generate a project report.
-   [x] Derive research queries and retrieve candidate arXiv papers.
-   [x] Rank candidate papers and attempt limited PDF extraction.
-   [x] Provide a fallback report when AI synthesis is unavailable.
-   [x] Add initial automated research-pipeline tests.
-   [x] Verify direct API access to the configured Gemma model.
-   [ ] Verify end-to-end restart-plan generation with Gemma.
-   [ ] Expand end-to-end tests and edge-case handling.
-   [ ] Improve evidence traceability and paper-relevance explanations.
-   [ ] Polish responsive UI states and error messages.
-   [ ] Publish a reproducible demo and walkthrough.

## Contributing

Issues and pull requests are welcome. Useful contributions include
additional repository fixtures, tests for unusual Git states,
improvements to research relevance, clearer evidence attribution, and
documentation.

Before opening a pull request:

1.  Run the test suite.
2.  Do not commit `.env`, API keys, private repository data, or
    sensitive generated reports.
3.  Describe the change and how it was tested.

