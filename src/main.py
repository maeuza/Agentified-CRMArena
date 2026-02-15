# --- RUTAS DE IDENTIDAD (GET) ---
@app.route("/agent-card.json", methods=["GET"])
async def get_agent_card(request):
    """Sirve el archivo de identidad del agente."""
    file_path = "agent-card.json"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"error": "File not found"}, status_code=404)

@app.route("/.well-known/agent-card.json", methods=["GET"])
async def get_well_known_card(request):
    return await get_agent_card(request)

# --- RUTAS DE EJECUCIÓN (POST) ---
# Hemos añadido la ruta "/" para que el evaluador no reciba un 404
@app.route("/a2a-delivery", methods=["POST"])
@app.route("/", methods=["POST"]) 
async def delivery(request):
    try:
        data = await request.json()
        params = data.get("params", {})
        task_text = params.get("task", "Listar casos")
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
        print(f"❌ Error crítico: {e}")
        return JSONResponse({
            "jsonrpc": "2.0", 
            "error": {"code": -32603, "message": str(e)}, 
            "id": data.get("id") if 'data' in locals() else None
        }, status_code=200)