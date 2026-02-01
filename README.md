# CRMArena: Reliable Salesforce Agent Benchmark (A2A)

This repository implements a **Green Agent (Evaluator)** and a **Purple Agent (Participant)** for the AgentBeats competition, based on the CRMArena benchmark. It is optimized for **reliability and speed** by using a local data infrastructure.

## 🌟 Key Features

* **Reliable Evaluation (Offline-First):** Uses a local SQLite database (`crmarena_data.db`) to validate records, ensuring 100% uptime and bypassing external API rate limits or connectivity issues.
* **Integrated Dataset:** Automated consumption of the `Salesforce/CRMArena` dataset from Hugging Face (test partition).
* **Advanced Tool Use:** The participant is equipped with SOQL-compatible tools to query the local CRM mock, demonstrating real-world data handling.
* **Dual A2A Architecture:** A single container handles both **Judge (Green)** and **Participant (Purple)** roles via environment variables.



## 📂 Project Structure

* `src/agent.py`: The **Green Agent** logic. It pulls tasks from HuggingFace and scores the participant.
* `src/participant.py`: The **Purple Agent** logic. Powered by Gemini 1.5 Flash and LangChain.
* `src/functions.py`: Toolset for SQLite/SOQL querying and CRM logic (AHT calculation, workload analysis).
* `src/local_data/`: Directory containing the `crmarena_data.db` SQLite file.
* `src/main.py`: Unified entry point using `AGENT_ROLE` to switch modes.

## ⚙️ Configuration & Requirements

### 1. Environment Variables
Configure these in your **AgentBeats/GitHub Secrets**:
* `GOOGLE_API_KEY`: Required for the Gemini model.
* `AGENT_ROLE`: Set to `green` for the Evaluator or `purple` for the Participant.

### 2. Dependencies
Main libraries used:
* `langchain-google-genai`
* `a2a-protocol`
* `python-dateutil`
* `sqlite3`
* `pandas`

## 📦 Local Execution

Verify the system health locally using Docker:


# Build the image
docker build -t crm-arena-pro .

# Run as Participant (Reference Agent)
docker run -p 8000:8000 -e GOOGLE_API_KEY="your_key" -e AGENT_ROLE=purple crm-arena-pro


Binary Accuracy: Strict comparison between the agent's response and the dataset's ground_truth. 


Task Metadata: Logging of persona and query types for nuanced analysis. 


Robustness: Error handling for API communication and data schema validation.
