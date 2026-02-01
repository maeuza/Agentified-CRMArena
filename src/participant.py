import os
from a2a.utils import get_message_text, new_agent_text_message
from a2a.types import Message
from langchain_google_genai import ChatGoogleGenerativeAI
import functions # This imports your sqlite3 logic

class Participant:
    def __init__(self):
        # We bind the tools from your functions.py to the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        # Bind the issue_soql_query tool so Gemini can use it
        self.llm_with_tools = self.llm.bind_tools([functions.issue_soql_query])

    async def run(self, message: Message, updater=None) -> Message:
        query = get_message_text(message)
        
        system_prompt = (
            "You are a Salesforce CRM expert. Use the provided tools to query the database "
            "and answer the user's question accurately based on the data. Answer in English."
        )
        
        # Here Gemini decides if it needs to call your issue_soql_query function
        ai_msg = self.llm_with_tools.invoke(f"{system_prompt}\n\nQuestion: {query}")
        
        # Logic to handle tool calls and return the final answer
        if ai_msg.tool_calls:
            for tool_call in ai_msg.tool_calls:
                selected_tool = {"issue_soql_query": functions.issue_soql_query}[tool_call["name"].lower()]
                tool_output = selected_tool(**tool_call["args"])
                # Second pass to give the final answer with the data found
                final_answer = self.llm.invoke(f"Data found: {tool_output}\n\nUser Question: {query}")
                return new_agent_text_message(final_answer.content)
        
        return new_agent_text_message(ai_msg.content)