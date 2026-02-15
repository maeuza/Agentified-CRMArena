import os
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
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
        return JSONResponse({
            "jsonrpc": "2.0", 
            "error": {"code": -32603, "message": str(e)}, 
            "id": req_id
        }, status_code=200) # Devolvemos 200 para que PowerShell no lance excepción roja

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)