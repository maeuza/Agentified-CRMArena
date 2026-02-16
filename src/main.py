import os
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route
from executor import Executor

# --- MOCK PARA EL SDK ---
class UnifiedMock:
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

    async def enqueue_event(self, *args, **kwargs): pass
    async def send_message(self, *args, **kwargs): pass
    async def start_work(self): pass
    async def complete(self): pass
    async def failed(self, err): pass
    async def put(self, event): pass 

executor_instance = Executor()

# --- HANDLERS ---

async def get_agent_card(request):
    """Sirve la identidad del agente."""
    file_path = "agent-card.json"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "File not found"}, status_code=404)

async def delivery(request):
    """Manejador para POST / y POST /a2a-delivery."""
    try:
        data = await request.json()
        params = data.get("params", {})
        # Extraer la tarea del JSON-RPC o del body directo
        task_text = params.get("task", data.get("task", "Listar casos"))
        req_id = data.get("id")
        
        print(f"🤖 Tarea recibida: {task_text}")
        
        mock = UnifiedMock(task_text)
        result = await executor_instance.execute(mock, mock)
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": str(result),
            "id": req_id
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse({
            "jsonrpc": "2.0", 
            "error": {"code": -32603, "message": str(e)}, 
            "id": None
        })

# --- RUTAS ---
# Definimos explícitamente la raíz para POST
routes = [
    Route("/agent-card.json", get_agent_card, methods=["GET"]),
    Route("/.well-known/agent-card.json", get_agent_card, methods=["GET"]),
    Route("/a2a-delivery", delivery, methods=["POST"]),
    Route("/", delivery, methods=["POST"]),  # <--- ESTA ES LA RUTA CRÍTICA
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)