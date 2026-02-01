import os
from datasets import load_dataset
from a2a.utils import get_message_text, new_agent_text_message
from a2a.types import Message, Part, DataPart, TextPart
from messenger import Messenger

class Agent:
    def __init__(self):
        self.messenger = Messenger()
        # Cargamos el dataset oficial de CRMArena (HuggingFace)
        print("Loading official CRMArena benchmark...")
        self.dataset = load_dataset("Salesforce/CRMArena", "CRMArena", split="test")

    async def run(self, message: Message, updater):
        await updater.start_work()
        
        # Obtenemos la tarea (puedes configurar el task_id desde AgentBeats)
        task_id = 0 # O leer de un config
        current_task = self.dataset[task_id]
        question = current_task["query"]
        ground_truth = str(current_task["ground_truth"]).strip().lower()

        # El Verde le pregunta al Púrpura (Participant) en Inglés
        participant_url = os.getenv("PARTICIPANT_URL") 
        msg_to_send = new_agent_text_message(question)
        
        purple_response = await self.messenger.talk_to_agent(msg_to_send, participant_url)
        answer_text = get_message_text(purple_response).strip().lower()

        # Evaluación científica: ¿Está el resultado correcto dentro de la respuesta?
        is_correct = ground_truth in answer_text
        score = 1.0 if is_correct else 0.0

        # Reporte de resultados a la plataforma
        await updater.add_artifact(
            parts=[Part(root=DataPart(data={
                "score": score,
                "question": question,
                "agent_answer": answer_text,
                "correct_answer": ground_truth,
                "status": "Success" if is_correct else "Failed"
            }))]
        )
        await updater.complete()