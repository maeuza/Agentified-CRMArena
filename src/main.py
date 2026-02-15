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

    # Métodos de notificación que el Executor necesita para no dar error
    async def enqueue_event(self, *args, **kwargs): pass
    async def send_message(self, *args, **kwargs): pass
    async def start_work(self): pass
    async def complete(self): pass
    async def failed(self, err): pass

app = Starlette()
executor_instance = Executor()

# --- RUTAS DE IDENTIDAD (GET) ---
@app.route("/agent-card.json", methods=["GET"])
async def get_agent_card(request):
    """Sirve el archivo de identidad del agente."""
    # Buscamos el archivo en la raíz del contenedor
    file_path = "agent-card.json"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "Agent card not found"}, status_code=404)

@app.route("/.well-known/agent-card.json", methods=["GET"])
async def get_well_known_card(request):
    """Ruta estándar que el evaluador ya está encontrando con éxito (200 OK)."""
    return await get_agent_card(request)

# --- RUTAS DE EJECUCIÓN (POST) ---
# Usamos dos decoradores para capturar el POST en cualquier ubicación
@app.route("/a2a-delivery", methods=["POST"])
@app.route("/", methods=["POST"]) 
async def delivery(request):
    """
    Maneja la recepción de tareas. 
    Acepta el POST en la raíz para evitar el error 404 visto en los logs.
    """
    try:
        data = await request.json()
        params = data.get("params", {})
        
        # El evaluador suele enviar la tarea dentro de 'params' bajo la llave 'task'
        task_text = params.get("task", data.get("task", "Listar casos"))
        req_id = data.get("id")
        
        print(f"🤖 Procesando tarea en CRM-Arena: {task_text}")
        
        # Creamos el objeto mock para el flujo del executor
        mock_obj = SimpleMock(task_text)
        
        # Ejecutamos la lógica de Salesforce a través del Executor
        result = await executor_instance.execute(mock_obj, mock_obj)
        
        # Devolvemos la respuesta siguiendo el protocolo JSON-RPC 2.0
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": str(result),
            "id": req_id
        })
        
    except Exception as e:
        print(f"❌ Error crítico en delivery: {e}")
        # Intentamos recuperar el ID del request original para la respuesta de error
        try:
            body = await request.json()
            error_id = body.get("id")
        except:
            error_id = None
            
        return JSONResponse({
            "jsonrpc": "2.0", 
            "error": {"code": -32603, "message": str(e)}, 
            "id": error_id
        }, status_code=200)

if __name__ == "__main__":
    # Importante: host 0.0.0.0 para que Docker permita conexiones externas
    uvicorn.run(app, host="0.0.0.0", port=8000)