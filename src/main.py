import os
import uvicorn
from fastapi.responses import FileResponse

# --- BLOQUE DE IMPORTACIÓN ROBUSTA ---
try:
    # Intento 1: Ruta estándar del SDK actualizado
    from a2a import AgentServer
except ImportError:
    try:
        # Intento 2: Ruta interna en versiones específicas
        from a2a.server.app import AgentServer
    except ImportError:
        try:
            # Intento 3: Ruta alternativa de servidor
            from a2a.server import AgentServer
        except ImportError as e:
            print("❌ Error crítico: No se pudo encontrar AgentServer en la librería a2a.")
            print("Asegúrate de que 'a2a-sdk' esté correctamente instalado.")
            raise e
# -------------------------------------

from agent import Agent          
from participant import Participant

def main():
    """
    Entry point for the AgentBeats platform. 
    Determines if the instance should act as a Judge (Green) or a Worker (Purple).
    """
    # El rol se define por variable de entorno (green o purple)
    role = os.getenv("AGENT_ROLE", "purple").lower()
    
    print(f"--- Starting CRMArena Node ---")
    print(f"Active Role: {role.upper()}")

    # Inicializamos la lógica según el rol
    if role == "green":
        # El Juez (Carga dataset y evalúa)
        agent_instance = Agent()
    else:
        # El Participante (Usa Gemini y herramientas SQL)
        agent_instance = Participant()

    # Creamos el servidor compatible con el protocolo A2A
    server = AgentServer(agent_instance)

    # --- ENDPOINT PARA EL LEADERBOARD ---
    # Sirve el archivo de metadatos requerido para el benchmark
    @server.app.get("/agent-card.json")
    async def get_agent_card():
        # El archivo debe estar en la raíz del contenedor (/app/agent-card.json)
        return FileResponse("agent-card.json")
    # ------------------------------------
    
    print(f"Deployment Status: Online on port 8000")
    
    uvicorn.run(
        server.app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info"
    )

if __name__ == "__main__":
    main()