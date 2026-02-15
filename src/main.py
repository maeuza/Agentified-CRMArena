import os
import uvicorn
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse
from executor import Executor

# Mock Universal: Absorbe todas las llamadas del SDK de A2A
class SimpleMock:
    def __init__(self, text):
        self.message = text
        self.content = text
        self.task_id = "task-123"
        self.agent_role = "purple"
        self.current_task = self 
        self.state = "RUNNING"
        self.id = "msg-123"

    # Métodos de notificación que el Executor necesita
    async def enqueue_event(self, *args, **kwargs):
        pass # Simplemente ignora el evento de progreso
    
    async def send_message(self, *args, **kwargs):
        pass

    async def start_work(self): pass
    async def complete(self): pass
    async def failed(self, err): pass

app = Starlette()
executor_instance = Executor()

# --- NUEVAS RUTAS PARA SERVIR EL AGENT-CARD Y EVITAR EL 404 ---
@app.route("/agent-card.json", methods=["GET"])
async def get_agent_card(request):
    """Sirve el archivo de identidad del agente."""
    file_path = "agent-card.json"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        # Fallback por si el archivo no está en la raíz del contenedor
        return JSONResponse({
            "name": "CRM-Arena-L1-Agent",
            "version": "1.0.0",
            "endpoints": {"a2a": "/a2a-delivery"}
        }, status_code=200)

@app.route("/.well-known/agent-card.json", methods=["GET"])
async def get_well_known_card(request):
    """Ruta estándar adicional que suelen buscar los evaluadores."""
    return await get_agent_card(request)
# -----------------------------------------------------------

@app.route("/a2a-delivery", methods=["POST"])
async def delivery(request):
    try:
        data = await request.json()
        params = data.get("params", {})
        # Extraemos la tarea del JSON-RPC
        task_text = params.get("task", "Listar casos")
        req_id = data.get("id")
        
        print(f"🤖 Procesando tarea en CRM-Arena: {task_text}")
        
        mock_obj = SimpleMock(task_text)
        
        # Ejecutamos el flujo completo
        result = await executor_instance.execute(mock_obj, mock_obj)
        
        # Devolvemos la respuesta en formato JSON-RPC 2.0
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": str(result),
            "id": req_id
        })
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        # Definimos req_id por si falla antes de extraerlo
        error_id = data.get("id") if 'data' in locals() else None
        return JSONResponse({
            "jsonrpc": "2.0", 
            "error": {"code": -32603, "message": str(e)}, 
            "id": error_id
        }, status_code=200)

if __name__ == "__main__":
    # Asegúrate de que el host sea 0.0.0.0 para Docker
    uvicorn.run(app, host="0.0.0.0", port=8000)