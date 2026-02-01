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
    """Format of the request sent by AgentBeats."""
    participants: dict[str, HttpUrl]  # role -> Agent URL
    config: dict[str, Any]

class Agent:
    # Defining competition requirements
    required_roles: list[str] = ["crm_participant"]
    required_config_keys: list[str] = ["task_id"]

    def __init__(self):
        self.messenger = Messenger()
        
        # 1. DATASET LOADING (The Exam)
        print("Loading CRMArena dataset from Hugging Face...")
        self.dataset = load_dataset("Salesforce/CRMArena", "CRMArena", split="test")

        # 2. SALESFORCE CONNECTION (Secure via Environment Variables)
        sf_user = os.getenv("SALESFORCE_USERNAME")
        sf_pass = os.getenv("SALESFORCE_PASSWORD")
        sf_token = os.getenv("SALESFORCE_SECURITY_TOKEN")

        # Security check: If any are missing, raise a clear error
        if not all([sf_user, sf_pass, sf_token]):
            raise ValueError(
                "CONFIGURATION ERROR: Salesforce credentials missing. "
                "Please ensure SALESFORCE_USERNAME, PASSWORD, and TOKEN are set."
            )

        try:
            self.sf = Salesforce(
                username=sf_user, 
                password=sf_pass, 
                security_token=sf_token
            )
            print("Secure connection established with Salesforce.")
        except Exception as e:
            print(f"Critical error connecting to Salesforce: {e}")

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        """Validates that the request has the necessary roles and config keys."""
        missing_roles = set(self.required_roles) - set(request.participants.keys())
        if missing_roles:
            return False, f"Missing roles: {missing_roles}"

        missing_config_keys = set(self.required_config_keys) - set(request.config.keys())
        if missing_config_keys:
            return False, f"Missing configuration keys: {missing_config_keys}"

        return True, "ok"

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Main evaluation logic."""
        input_text = get_message_text(message)

        # A. Validate request structure
        try:
            request: EvalRequest = EvalRequest.model_validate_json(input_text)
            ok, msg = self.validate_request(request)
            if not ok:
                await updater.reject(new_agent_text_message(msg))
                return
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Invalid request: {e}"))
            return

        # B. Search for the task in the dataset
        task_id = request.config.get("task_id")
        # Find the row that matches the provided ID
        current_task = next((item for item in self.dataset if item["id"] == task_id), None)

        if not current_task:
            await updater.reject(new_agent_text_message(f"Task ID {task_id} not found in CRMArena."))
            return

        question = current_task["query"]
        ground_truth = current_task["ground_truth"]

        await updater.update_status(
            TaskState.working, 
            new_agent_text_message(f"Starting CRMArena evaluation for task: {task_id}")
        )

        # C. A2A Interaction with Participant Agent (Purple)
        participant_url = request.participants["crm_participant"]
        msg_to_send = new_agent_text_message(question)
        
        # Send query and wait for response
        purple_response_msg = await self.messenger.talk_to_agent(msg_to_send, participant_url)
        answer_text = get_message_text(purple_response_msg)

        # D. Scoring (Comparison with Ground Truth)
        # Strip whitespace and lowercase for a fair comparison
        is_correct = answer_text.strip().lower() == str(ground_truth).strip().lower()
        score = 1.0 if is_correct else 0.0

        # E. Report Final Artifact
        # This result will be stored and displayed by the platform
        await updater.add_artifact(
            parts=[
                Part(root=TextPart(text=f"Evaluation completed for task {task_id}.")),
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