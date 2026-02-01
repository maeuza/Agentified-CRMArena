import os
from datasets import load_dataset
from a2a.utils import get_message_text, new_agent_text_message
from a2a.types import Message, Part, DataPart
from messenger import Messenger

class Agent:
    def __init__(self):
        self.messenger = Messenger()
        self.dataset = None  # lazy load

    async def run(self, message: Message, updater):
        # SSE handshake inmediato
        await updater.start_work()
        await updater.add_artifact(
            parts=[Part(root=DataPart(data={"status": "started"}))]
        )

        if self.dataset is None:
            self.dataset = load_dataset(
                "Salesforce/CRMArena", "CRMArena", split="test"
            )

        task_id = 0
        current_task = self.dataset[task_id]
        question = current_task["query"]
        ground_truth = str(current_task["ground_truth"]).strip().lower()

        await updater.add_artifact(
            parts=[Part(root=DataPart(data={"status": "querying participant"}))]
        )

        participant_url = os.getenv("PARTICIPANT_URL")
        msg_to_send = new_agent_text_message(question)

        purple_response = await self.messenger.talk_to_agent(
            msg_to_send, participant_url
        )

        answer_text = get_message_text(purple_response).strip().lower()
        is_correct = ground_truth in answer_text
        score = 1.0 if is_correct else 0.0

        await updater.add_artifact(
            parts=[Part(root=DataPart(data={
                "score": score,
                "question": question,
                "agent_answer": answer_text,
                "correct_answer": ground_truth,
                "status": "Success" if is_correct else "Failed"
            })))]
        )

        await updater.complete()
