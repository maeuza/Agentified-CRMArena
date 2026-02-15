import os
import uvicorn
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route
from executor import Executor

# Mock mejorado para cumplir con RequestContext y EventQueue
class UnifiedMock:
    def __init__(self, text):
        # Para context.message y context.current_task
        self.message = text
        self.content = text
        self.task_id = "task-123"
        self.id = "task-123"
        self.agent_role = "purple"
        self.current_task = self 
        self.status = self
        self.state = "RUNNING"
        self.context_id = "ctx-default"

    # Métodos requeridos por el Executor y TaskUpdater (EventQueue)
    async def enqueue_event(self, *args, **kwargs): pass
    async def send_message(self, *args, **kwargs): pass
    async def start_work(self): pass
    async def complete(self): pass
    async def failed(self, err): pass
    async def put(self, event): pass # Requerido por algunos flujos de EventQueue

executor_instance = Executor()

async def get_agent_card(request):
    file_path = "agent-card.json"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "File not found"}, status_code=404)

async def delivery(request):
    try:
        data = await request.json()
        # Manejo de JSON-RPC 2.0: la tarea suele venir en params['task']
        params = data.get("params", {})
        task_text = params.get("task", data.get("task", "Listar casos"))
        req_id = data.get("id")
        
        print(f"🤖 Recibido en Root/Delivery: {task_text}")
        
        # Creamos el objeto que simula tanto el contexto como la cola de eventos
        unified_obj = UnifiedMock(task_text)
        
        # Llamamos al executor
        result = await executor_instance.execute(unified_obj, unified_obj)
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": str(result),
            "id": req_id
        })
    except Exception as e:
        print(f"❌ Error en delivery: {e}")
        return JSONResponse({
            "jsonrpc": "2.0", 
            "error": {"code": -32603, "message": str(e)}, 
            "id": None
        }, status_code=200) # Importante: JSON-RPC responde 200 aunque haya error de app

routes = [
    Route("/agent-card.json", get_agent_card, methods=["GET"]),
    Route("/.well-known/agent-card.json", get_agent_card, methods=["GET"]),
    Route("/a2a-delivery", delivery, methods=["POST"]),
    Route("/", delivery, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)