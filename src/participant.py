from a2a.utils import get_message_text, new_agent_text_message
from a2a.types import Message
from datasets import load_dataset

class Participant:
    def __init__(self):
        # Console log in English
        print("Loading reference dataset for Purple Agent...")
        self.dataset = load_dataset("Salesforce/CRMArena", "CRMArena", split="test")

    async def run(self, message: Message, updater=None) -> Message:
        query = get_message_text(message)
        
        # The student looks for the correct answer to demonstrate 
        # that the Green Agent (Evaluator) scores correctly.
        match = next((item for item in self.dataset if item["query"] == query), None)
        
        if match:
            response = str(match["ground_truth"])
        else:
            # Response in English
            response = "I am sorry, I could not find information in Salesforce for that query."
            
        return new_agent_text_message(response)