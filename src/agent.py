import os
from datasets import load_dataset
from a2a.utils import get_message_text, new_agent_text_message
from a2a.types import Message, Part, DataPart
from messenger import Messenger

class Agent:
    def __init__(self):
        self.messenger = Messenger()
        self.dataset = None  

    async def run(self, message: Message, updater):
        # 1. Handshake inicial (Obligatorio para AgentBeats)
        await updater.start_work()
        
        # 2. Carga segura del dataset
        if self.dataset is None:
            try:
                print("--- Cargando dataset de CRMArena ---")
                # Cargamos solo la partición 'test'
                self.dataset = load_dataset(
                    "Salesforce/CRMArena", "Salesforce-CRMArena", split="test", trust_remote_code=True
                )
            except Exception as e:
                error_msg = f"Error crítico cargando dataset: {e}"
                await updater.failed(new_agent_text_message(error_msg))
                return

        # 3. Selección de la tarea
        # Por defecto tomamos la primera tarea del benchmark
        task_id = 0 
        current_task = self.dataset[task_id]
        question = current_task["query"]
        ground_truth = str(current_task["ground_truth"]).strip().lower()

        # 4. Comunicación con el Participante (Purple Agent)
        participant_url = os.getenv("PARTICIPANT_URL")
        if not participant_url:
            await updater.failed(new_agent_text_message("Error: PARTICIPANT_URL no configurada"))
            return

        print(f"Enviando pregunta al participante: {question}")
        msg_to_send = new_agent_text_message(question)

        try:
            purple_response = await self.messenger.talk_to_agent(
                msg_to_send, participant_url
            )
            answer_text = get_message_text(purple_response).strip().lower()
            
            # 5. Evaluación (Lógica de scoring)
            # Verificamos si la respuesta correcta está contenida en la respuesta del agente
            is_correct = ground_truth in answer_text
            score = 1.0 if is_correct else 0.0

            # 6. Reporte de resultados al Leaderboard
            await updater.add_artifact(
                parts=[Part(root=DataPart(data={
                    "score": score,
                    "question": question,
                    "expected": ground_truth,
                    "received": answer_text
                }))]
            )
            await updater.complete()
            
        except Exception as e:
            print(f"Fallo en la comunicación: {e}")
            await updater.failed(new_agent_text_message(f"Error de evaluación: {e}"))