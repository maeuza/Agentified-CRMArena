import os
import uvicorn
from a2a.server.app import AgentServer
from agent import Agent          
from participant import Participant

def main():
    # Read the environment variable to be configured in AgentBeats
    # Defaults to 'green' (evaluator) if the variable is not found
    role = os.getenv("AGENT_ROLE", "green").lower()
    
    print(f"--- Starting Agent in {role.upper()} mode ---")

    if role == "green":
        # Launch the evaluation logic (Green Agent)
        agent_instance = Agent()
    else:
        # Launch the reference participant logic (Purple Agent)
        agent_instance = Participant()

    # Create the web server compatible with the A2A protocol
    server = AgentServer(agent_instance)
    
    # Run the server on port 8000
    # Note: Ensure this port matches your Dockerfile EXPOSE command
    print(f"Serving A2A Agent on port 8000...")
    uvicorn.run(server.app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()