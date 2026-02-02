import os
import functions  # Tu lógica de SQLite
from a2a.utils import get_message_text, new_agent_text_message
from a2a.types import Message
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

class Participant:
    def __init__(self):
        # Usamos Gemini 1.5 Flash por su velocidad y bajo costo
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0  # Vital para que el SOQL sea consistente
        )
        
        # Mapeo de herramientas disponibles
        self.tools = {
            "issue_soql_query": functions.issue_soql_query,
            "get_agents_with_max_cases": functions.get_agents_with_max_cases,
            "calculate_average_handle_time": functions.calculate_average_handle_time
        }
        
        # Vinculamos todas las herramientas de functions.py
        self.llm_with_tools = self.llm.bind_tools(list(self.tools.values()))

    async def run(self, message: Message, updater=None) -> Message:
        query_text = get_message_text(message)
        
        # El System Prompt es la clave para CRM Arena L1
        system_prompt = (
            "You are a Salesforce Expert. You have access to a local CRM database via SOQL.\n"
            "SCHEMA CONTEXT:\n"
            "- Objects: Case, Account, Contact, User, KnowledgeArticle, etc.\n"
            "- For 'Routing' tasks: Always return the ID of the User/Agent.\n"
            "- For 'QA' tasks: Be concise and base your answer ONLY on the retrieved data.\n"
            "INSTRUCTIONS:\n"
            "1. Generate a valid SOQL query for the user's request.\n"
            "2. Execute the tool and analyze the results.\n"
            "3. If no data is found, state it clearly."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query_text)
        ]

        # Primera llamada: Gemini decide qué herramienta usar
        ai_msg = self.llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        # Procesar llamadas a herramientas (Loop de ejecución)
        if ai_msg.tool_calls:
            for tool_call in ai_msg.tool_calls:
                tool_name = tool_call["name"].lower()
                tool_args = tool_call["args"]
                
                # Ejecutar la función real
                if tool_name in self.tools:
                    observation = self.tools[tool_name](**tool_args)
                    
                    # Añadir el resultado al historial para que Gemini lo lea
                    messages.append(ToolMessage(
                        content=str(observation), 
                        tool_call_id=tool_call["id"]
                    ))

            # Segunda llamada: Gemini genera la respuesta final basada en los datos
            final_response = self.llm.invoke(messages)
            return new_agent_text_message(final_response.content)
        
        # Si no necesitó herramientas, devolvemos la respuesta directa
        return new_agent_text_message(ai_msg.content)