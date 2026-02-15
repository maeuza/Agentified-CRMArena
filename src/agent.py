from participant import Participant 
from a2a.utils import get_message_text

class Agent:
    def __init__(self):
        self.participant = Participant()

    async def run(self, message, updater):
        # Aseguramos que message sea un string puro
        text_input = get_message_text(message) if not isinstance(message, str) else message
        
        await updater.start_work()
        try:
            # Enviamos el texto al participante (Salesforce logic)
            response_text = await self.participant.run(text_input)
            # NO llamamos a complete() aquí, dejamos que Executor lo maneje
            return str(response_text)
        except Exception as e:
            await updater.failed(f"Fallo: {str(e)}")
            return f"Error en Agente: {str(e)}"