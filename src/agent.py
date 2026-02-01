import os
import json
from typing import Any
from pydantic import BaseModel, HttpUrl, ValidationError
from datasets import load_dataset
from simple_salesforce import Salesforce

from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart, DataPart
from a2a.utils import get_message_text, new_agent_text_message
from messenger import Messenger

class EvalRequest(BaseModel):
    """Formato de petición enviado por AgentBeats."""
    participants: dict[str, HttpUrl]  # rol -> URL del agente
    config: dict[str, Any]

class Agent:
    # Definimos los requisitos para el concurso
    required_roles: list[str] = ["crm_participant"]
    required_config_keys: list[str] = ["task_id"]

    def __init__(self):
        self.messenger = Messenger()
        
        # 1. CARGA DEL DATASET (Examen)
        print("Cargando dataset de CRMArena desde Hugging Face...")
        self.dataset = load_dataset("Salesforce/CRMArena", "CRMArena", split="test")

        # 2. CONEXIÓN A SALESFORCE (Segura mediante Variables de Entorno)
        sf_user = os.getenv("SALESFORCE_USERNAME")
        sf_pass = os.getenv("SALESFORCE_PASSWORD")
        sf_token = os.getenv("SALESFORCE_SECURITY_TOKEN")

        # Verificación de seguridad: Si falta alguna, lanzamos un error claro
        if not all([sf_user, sf_pass, sf_token]):
            raise ValueError(
                "ERROR DE CONFIGURACIÓN: Faltan credenciales de Salesforce. "
                "Asegúrate de configurar SALESFORCE_USERNAME, PASSWORD y TOKEN."
            )

        try:
            self.sf = Salesforce(
                username=sf_user, 
                password=sf_pass, 
                security_token=sf_token
            )
            print("Conexión segura establecida con Salesforce.")
        except Exception as e:
            print(f"Error crítico al conectar a Salesforce: {e}")

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        """Valida que la petición tenga los roles y llaves de config necesarios."""
        missing_roles = set(self.required_roles) - set(request.participants.keys())
        if missing_roles:
            return False, f"Faltan roles: {missing_roles}"

        missing_config_keys = set(self.required_config_keys) - set(request.config.keys())
        if missing_config_keys:
            return False, f"Faltan llaves de configuración: {missing_config_keys}"

        return True, "ok"

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Lógica principal de evaluación."""
        input_text = get_message_text(message)

        # A. Validar la estructura de la petición
        try:
            request: EvalRequest = EvalRequest.model_validate_json(input_text)
            ok, msg = self.validate_request(request)
            if not ok:
                await updater.reject(new_agent_text_message(msg))
                return
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Petición inválida: {e}"))
            return

        # B. Buscar la tarea en el dataset
        task_id = request.config.get("task_id")
        # Buscamos la fila que coincida con el ID proporcionado
        current_task = next((item for item in self.dataset if item["id"] == task_id), None)

        if not current_task:
            await updater.reject(new_agent_text_message(f"Task ID {task_id} no encontrado en CRMArena."))
            return

        question = current_task["query"]
        ground_truth = current_task["ground_truth"]

        await updater.update_status(
            TaskState.working, 
            new_agent_text_message(f"Iniciando evaluación de CRMArena: {task_id}")
        )

        # C. Interacción A2A con el Agente Participante (Púrpura)
        participant_url = request.participants["crm_participant"]
        msg_to_send = new_agent_text_message(question)
        
        # Enviamos la pregunta y esperamos respuesta
        purple_response_msg = await self.messenger.talk_to_agent(msg_to_send, participant_url)
        answer_text = get_message_text(purple_response_msg)

        # D. Calificación (Comparación con Ground Truth)
        # Limpiamos espacios y pasamos a minúsculas para una comparación justa
        is_correct = answer_text.strip().lower() == str(ground_truth).strip().lower()
        score = 1.0 if is_correct else 0.0

        # E. Reportar el Artefacto Final
        # Este es el resultado que la plataforma guardará y mostrará
        await updater.add_artifact(
            parts=[
                Part(root=TextPart(text=f"Evaluación finalizada para la tarea {task_id}.")),
                Part(root=DataPart(data={
                    "task_id": task_id,
                    "persona": current_task.get("persona", "Unknown"),
                    "score": score,
                    "correct_answer": ground_truth,
                    "agent_answer": answer_text,
                    "is_match": is_correct,
                    "benchmark": "CRMArena"
                }))
            ],
            name="CRMArena Evaluation Report",
        )