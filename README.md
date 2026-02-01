CRMArena-Pro: Salesforce Agent Benchmark (A2A)
This repository implements a high-performance Green Agent (Evaluator) for the AgentBeats competition, based on Salesforce's CRMArena benchmark. Its goal is to measure the reasoning and execution capabilities of LLM agents in complex, real-world CRM tasks. 

 Key Features

Enterprise-Grade Evaluation: Secure connection to the Salesforce API to validate the real-time state of records. 


Integrated Dataset: Automated consumption of Salesforce/CRMArena from Hugging Face (1,170 test task partition). 


Dual A2A Architecture: The same container can act as a Judge (Green) or a Reference Participant (Purple) via environment variables. 


Detailed Reporting: Generates data artifacts including accuracy metrics (is_match) and task context data. 

Project Structure

src/agent.py: Implementation of the Green Agent with evaluation and scoring logic. 


src/participant.py: Purple Agent baseline demonstrating benchmark compatibility. 


src/main.py: Unified entry point managing the agent's role based on the environment. 


src/executor.py: A2A request handler following the protocol standards. 


Dockerfile: Configuration for autonomous and reproducible execution. 

Configuration & Requirements
1. Environment Variables (.env)
To enable Salesforce validation, configure the following credentials (do not commit to GitHub): 


SALESFORCE_USERNAME: Trial Org username. 


SALESFORCE_PASSWORD: User password. 


SALESFORCE_SECURITY_TOKEN: API security token. 

2. Role Selection (AgentBeats)
Set the AGENT_ROLE variable in the platform to determine the container's function: 


green: Activates Evaluator mode (Judge). 


purple: Activates Participant mode (Reference student). 

📦 Local Execution
Build and run the container to verify system health: 

Bash
# Build the image
docker build -t crm-arena-agent .

# Run as Evaluator (Port 8000)
docker run -p 8000:8000 --env-file .env -e AGENT_ROLE=green crm-arena-agent
📊 Scoring Methodology
The evaluation captures multiple performance dimensions: 


Binary Accuracy: Strict comparison between the agent's response and the dataset's ground_truth. 


Task Metadata: Logging of persona and query types for nuanced analysis. 


Robustness: Error handling for API communication and data schema validation.