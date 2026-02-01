import os
import uvicorn
from a2a.server.app import AgentServer
from agent import Agent          
from participant import Participant
def main():
    # Leemos la variable de entorno que configuraremos en AgentBeats
    # Si no hay variable, por defecto será el evaluador (green)
    role = os.getenv("AGENT_ROLE", "green").lower()
    
    print(f"--- Iniciando Agente en modo: {role.upper()} ---")

    if role == "green":
        # Arranca la lógica de evaluación que ya programamos
        agent_instance = Agent()
    else:
        # Arranca la lógica del participante de referencia
        agent_instance = Participant()

    # Creamos el servidor web compatible con el protocolo A2A
    server = AgentServer(agent_instance)
    
    # Ejecutamos el servidor en el puerto 8000
    uvicorn.run(server.app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()