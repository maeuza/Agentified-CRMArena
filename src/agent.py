from participant import Participant 
from a2a.utils import get_message_text

class Agent:
    def __init__(self):
        self.participant = Participant()

    async def run(self, message, updater):
        await updater.start_work()
        try:
            # Enviamos el mensaje al participante y retornamos el texto puro
            response_text = await self.participant.run(message)
            await updater.complete()
            return str(response_text)
        except Exception as e:
            await updater.failed(f"Fallo: {str(e)}")
            return f"Error en Agente: {str(e)}"