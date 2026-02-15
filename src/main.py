import os
import uvicorn
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route
from executor import Executor

# --- MOCK ROBUSTO PARA EL SDK DE A2A ---
class UnifiedMock:
    """Simula tanto el RequestContext como el EventQueue para el Executor."""
    def __init__(self, text):
        self.message = text
        self.content = text
        self.id = "task-123"
        self.task_id = "task-123"
        self.agent_role = "purple"
        self.current_task = self 
        self.status = self
        self.state = "RUNNING"
        self.context_id = "ctx-default"

    # Métodos requeridos por AgentExecutor y TaskUpdater
    async def enqueue_event(self, *args, **kwargs): pass
    async def send_message(self, *args, **kwargs): pass
    async def start_work(self): pass
    async def complete(self): pass
    async def failed(self, err): pass
    async def put(self, event): pass 

executor_instance = Executor()

# --- MANEJADORES (HANDLERS) ---

async def get_agent_card(request):
    """Sirve el archivo agent-card.json para la identificación del agente."""
    file_path = "agent-card.json"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "File not found"}, status_code=404)

async def delivery(request):
    """Manejador principal para las tareas del evaluador (POST)."""
    try:
        data = await request.json()
        
        # El evaluador suele enviar la tarea dentro de 'params' (JSON-RPC 2.0)
        params = data.get("params", {})
        task_text = params.get("task", data.get("task", "Listar casos de Salesforce"))
        req_id = data.get("id")
        
        print(f"🤖 Recibido en delivery: {task_text}")
        
        # Creamos el objeto unificado que el Executor espera
        unified_obj = UnifiedMock(task_text)
        
        # Ejecutamos la lógica que conecta con Salesforce/SQLite
        result = await executor_instance.execute(unified_obj, unified_obj)
        
        # Respuesta estándar JSON-RPC
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": str(result),
            "id": req_id
        })
        
    except Exception as e:
        print(f"❌ Error procesando POST: {e}")
        return JSONResponse({
            "jsonrpc": "2.0", 
            "error": {"code": -32603, "message": str(e)}, 
            "id": None
        })

# --- CONFIGURACIÓN DE RUTAS ---
# Definimos las rutas explícitamente para evitar el error 404
routes = [
    Route("/agent-card.json", get_agent_card, methods=["GET"]),
    Route("/.well-known/agent-card.json", get_agent_card, methods=["GET"]),
    Route("/a2a-delivery", delivery, methods=["POST"]),
    Route("/", delivery, methods=["POST"]), # Ruta raíz obligatoria para el evaluador
]

# Creamos la aplicación con las rutas y modo debug
app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    # Importante: host 0.0.0.0 y puerto 8000 para Docker
    uvicorn.run(app, host="0.0.0.0", port=8000)