import os
import uvicorn
from a2a.server.app import AgentServer
from agent import Agent          
from participant import Participant

def main():
    """
    Entry point for the AgentBeats platform. 
    Determines if the instance should act as a Judge (Green) or a Worker (Purple).
    """
    # Role assigned by AgentBeats environment variables
    role = os.getenv("AGENT_ROLE", "purple").lower()
    
    print(f"--- Starting CRMArena Node ---")
    print(f"Active Role: {role.upper()}")

    # Initialize the corresponding logic
    if role == "green":
        agent_instance = Agent()
    else:
        agent_instance = Participant()

    # Create the A2A-compliant server
    server = AgentServer(agent_instance)
    
    # Standard configuration for AgentBeats container deployment
    print(f"Deployment Status: Online on port 8000")
    
    uvicorn.run(
        server.app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info"
    )

if __name__ == "__main__":
    main()