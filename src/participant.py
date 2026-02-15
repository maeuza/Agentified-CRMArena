import asyncio
import os
import functions
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

class Participant:
    def __init__(self):
        self.model_name = "gemini-3-flash-preview"
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        # Temperatura 0 para evitar que la IA invente parámetros
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0
        )
        
        # Registro de funciones disponibles
        self.tools = [
            functions.issue_soql_query,
            functions.search_in_all_databases,
            functions.get_agents_with_max_cases,
            functions.calculate_average_handle_time,
            functions.generate_performance_report
        ]
        
        # Mapeo por nombre exacto para que coincida con tool_calls
        self.tools_map = {t.__name__: t for t in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def run(self, message) -> str:
        # Extraer el texto del mensaje entrante
        query_text = message.content if hasattr(message, 'content') else str(message)
        
        system_prompt = (
            "Eres el experto de CRM Arena. REGLAS ESTRICTAS:\n"
            "1. SQL: Usa siempre '\"Case\"' (con comillas dobles) para la tabla Case en SQLite.\n"
            "2. ARGUMENTOS: Solo pasa parámetros que existan exactamente en la firma de la función.\n"
            "3. VALORES EXACTOS: Status='Closed', Priority='High' (sin comillas extra en el valor).\n"
            "4. TIEMPO PROMEDIO: Para calcular tiempo promedio de resolución SIEMPRE usa "
            "calculate_average_handle_time, nunca construyas tu propio SQL para esto.\n"
            "5. DB B2C: Si mencionan B2C, usa issue_soql_query con db_type='b2c'.\n"
            "6. RESULTADO VACÍO: Si una herramienta devuelve [] o None, intenta con "
            "search_in_all_databases antes de concluir que no hay datos."
        )

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=query_text)]

        # Loop agentic: continúa hasta que el modelo dé respuesta sin tool_calls
        # o se alcance el límite de seguridad de iteraciones
        MAX_ITERATIONS = 6
        iteration = 0

        try:
            while iteration < MAX_ITERATIONS:
                iteration += 1
                await asyncio.sleep(1)
                # Siempre usar llm_with_tools para que el modelo pueda encadenar llamadas
                ai_msg = self.llm_with_tools.invoke(messages)
                messages.append(ai_msg)

                # Si no hay tool_calls, el modelo ya tiene la respuesta final
                if not ai_msg.tool_calls:
                    print(f"[Participant] Respuesta final tras {iteration} iteracion(es).")
                    return str(ai_msg.content)

                # Ejecutar TODAS las herramientas solicitadas en este turno
                for tool_call in ai_msg.tool_calls:
                    t_name = tool_call["name"]
                    t_args = tool_call["args"]
                    print(f"[Participant] Tool call #{iteration}: {t_name}({t_args})")

                    if t_name in self.tools_map:
                        res = self.tools_map[t_name](**t_args)
                    else:
                        res = f"Error: herramienta '{t_name}' no encontrada."

                    print(f"[Participant] Resultado de {t_name}: {str(res)[:300]}")
                    messages.append(
                        ToolMessage(content=str(res), tool_call_id=tool_call["id"])
                    )

            # Si se agotaron las iteraciones, forzar respuesta con lo que hay
            print(f"[Participant] Limite de {MAX_ITERATIONS} iteraciones alcanzado.")
            final_res = self.llm.invoke(messages)
            return str(final_res.content)

        except Exception as e:
            print(f"[Participant] Excepcion: {e}")
            return f"Fallo en ejecucion: {str(e)}"