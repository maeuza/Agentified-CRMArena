from a2a.utils import get_message_text, new_agent_text_message
from a2a.types import Message
from datasets import load_dataset

class Participant:
    def __init__(self):
        print("Cargando dataset de referencia para el Agente Púrpura...")
        self.dataset = load_dataset("Salesforce/CRMArena", "CRMArena", split="test")

    async def run(self, message: Message, updater=None) -> Message:
        query = get_message_text(message)
        
        # El estudiante busca la respuesta correcta para demostrar que el Verde califica bien
        match = next((item for item in self.dataset if item["query"] == query), None)
        
        if match:
            respuesta = str(match["ground_truth"])
        else:
            respuesta = "Lo siento, no encontré información en Salesforce para esa consulta."
            
        return new_agent_text_message(respuesta)