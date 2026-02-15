import os
import uvicorn
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route
from executor import Executor

# Mock para el flujo interno
class SimpleMock:
    def __init__(self, text):
        self.message = text
        self.content = text
        self.task_id = "task-123"
        self.agent_role = "purple"
        self.current_task = self 
        self.state = "RUNNING"
        self.id = "msg-123"

    async def enqueue_event(self, *args, **kwargs): pass
    async def send_message(self, *args, **kwargs): pass
    async def start_work(self): pass
    async def complete(self): pass
    async def failed(self, err): pass

executor_instance = Executor()

# --- HANDLERS ---

async def get_agent_card(request):
    """Sirve el archivo agent-card.json"""
    file_path = "agent-card.json"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "File not found"}, status_code=404)

async def delivery(request):
    """Manejador principal de tareas (POST)"""
    try:
        data = await request.json()
        params = data.get("params", {})
        task_text = params.get("task", data.get("task", "Listar casos"))
        req_id = data.get("id")
        
        print(f"🤖 Procesando tarea en CRM-Arena: {task_text}")
        
        mock_obj = SimpleMock(task_text)
        result = await executor_instance.execute(mock_obj, mock_obj)
        
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

# --- CONFIGURACIÓN DE RUTAS EXPLÍCITAS ---
# Usamos una lista de rutas clara para que Starlette no se confunda
routes = [
    Route("/agent-card.json", get_agent_card, methods=["GET"]),
    Route("/.well-known/agent-card.json", get_agent_card, methods=["GET"]),
    Route("/a2a-delivery", delivery, methods=["POST"]),
    Route("/", delivery, methods=["POST"]),  # <--- ESTA ES LA QUE ESTÁ FALLANDO EN EL LOG
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)