import sqlite3
import os
from datetime import datetime

# Configuración de la ruta: Asegura que funcione en local y en el contenedor
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "local_data", "crmarena_data.db")

def issue_soql_query(query: str):
    """
    Ejecuta una consulta SQL/SOQL en la base de datos local de CRM Arena.
    Úsala para buscar registros de Case, Account, Contact, User o Knowledge.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Permite acceder por nombre de columna
        cursor = conn.cursor()
        
        # Limpieza básica de SOQL para SQLite
        # (Ej: SOQL usa 'LIMIT 10', SQLite también, pero SOQL es case-insensitive)
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        return f"Error en la base de datos local: {str(e)}. Verifica que los nombres de tablas y campos sean correctos."

def calculate_average_handle_time(case_ids: list):
    """
    Calcula el tiempo promedio de resolución (AHT) en minutos para una lista de IDs de casos.
    Indispensable para tareas de rol 'Manager' o 'Analista'.
    """
    if not case_ids:
        return 0.0
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Preparamos la consulta con placeholders para evitar inyección
        placeholders = ', '.join(['?'] * len(case_ids))
        query = f"SELECT CreatedDate, ClosedDate FROM Case WHERE Id IN ({placeholders})"
        
        cursor.execute(query, case_ids)
        rows = cursor.fetchall()
        conn.close()
        
        total_minutes = 0
        count = 0
        
        for row in rows:
            if row['CreatedDate'] and row['ClosedDate']:
                try:
                    # CRM Arena usa formato ISO '2024-01-01T12:00:00Z'
                    # Reemplazamos Z por +00:00 para que Python lo entienda
                    start = datetime.fromisoformat(row['CreatedDate'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(row['ClosedDate'].replace('Z', '+00:00'))
                    
                    diff = (end - start).total_seconds() / 60
                    total_minutes += diff
                    count += 1
                except ValueError:
                    continue
        
        return total_minutes / count if count > 0 else 0.0
    except Exception as e:
        return f"Error calculando AHT: {str(e)}"