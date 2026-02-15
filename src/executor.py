from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message
from agent import Agent

TERMINAL_STATES = {TaskState.completed, TaskState.canceled, TaskState.failed, TaskState.rejected}

class Executor(AgentExecutor):
    def __init__(self):
        super().__init__()
        self.agents: dict[str, Agent] = {} 

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> str:
        msg = context.message
        if not msg:
            return "Error: Mensaje vacío"

        task = context.current_task
        if task and hasattr(task, 'status') and hasattr(task.status, 'state'):
            if task.status.state in TERMINAL_STATES:
                return "Tarea ya finalizada"

        context_id = getattr(task, 'context_id', "ctx-default")
        agent = self.agents.get(context_id)
        if not agent:
            agent = Agent()
            self.agents[context_id] = agent

        task_id = getattr(task, 'id', "task-123")
        updater = TaskUpdater(event_queue, task_id, context_id)

        try:
            # Lógica de concurso: Usar Participant + SQLite local
            result_text = await agent.run(msg, updater)
            
            if not getattr(updater, '_terminal_state_reached', False):
                await updater.complete()
            
            return str(result_text) 
        except Exception as e:
            print(f"Error en Executor: {e}")
            return f"Error: {str(e)}"

    # ESTO ES LO QUE FALTABA: El método cancel para que Python no se queje
    async def cancel(self, task_id: str) -> None:
        print(f"Cancelación solicitada para la tarea: {task_id}")
        pass