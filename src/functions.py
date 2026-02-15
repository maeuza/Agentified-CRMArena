import sqlite3
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATHS = {
    "general": os.path.join(BASE_DIR, "local_data", "crmarena_data.db"),
    "b2b":     os.path.join(BASE_DIR, "local_data", "crmarenapro_b2b_data.db"),
    "b2c":     os.path.join(BASE_DIR, "local_data", "crmarenapro_b2c_data.db")
}


def _normalize_dates_in_db(conn):
    """
    Registra TO_ISO() en la conexión SQLite.
    Convierte '2021-06-07T10:50:00.000+0000' → '2021-06-07 10:50:00'
    También soporta el formato legacy 'DD/MM/YYYY HH:MM:SS a. m.'
    """
    def to_iso(date_str):
        if not date_str:
            return None
        s = str(date_str).strip()

        # Formato principal: ISO 8601 con milisegundos y timezone
        # Ej: 2021-06-07T10:50:00.000+0000  →  2021-06-07 10:50:00
        s = re.sub(r'([+-]\d{2}:?\d{2}|Z)$', '', s)   # quitar timezone
        s = re.sub(r'\.\d+$', '', s)                    # quitar milisegundos
        s = s.replace('T', ' ')                         # T → espacio

        # Formato legacy: DD/MM/YYYY HH:MM:SS a. m.
        s2 = re.sub(r'\s*[ap]\.\s*m\.', '', s, flags=re.IGNORECASE).strip()
        m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})', s2)
        if m:
            d, mo, y, h, mi, sec = m.groups()
            if 'p' in str(date_str).lower() and 'm' in str(date_str).lower():
                h = int(h)
                if h != 12:
                    h += 12
            return f"{y}-{int(mo):02d}-{int(d):02d} {int(h):02d}:{mi}:{sec}"

        return s  # ya normalizado (ISO sin T ni milisegundos)

    conn.create_function("TO_ISO", 1, to_iso)


def issue_soql_query(query: str, db_type: str = "b2c", **kwargs):
    """
    Ejecuta una consulta SQL en una base de datos específica (b2c, b2b o general).
    Registra TO_ISO() para manejar fechas ISO 8601 con milisegundos/timezone.
    """
    path = DB_PATHS.get(db_type, DB_PATHS["b2c"])

    # Corrección automática: tabla Case requiere comillas dobles en SQLite
    if re.search(r'\bFROM\s+Case\b', query, re.IGNORECASE):
        query = re.sub(r'\bFROM\s+Case\b', 'FROM "Case"', query, flags=re.IGNORECASE)

    try:
        conn = sqlite3.connect(path)
        _normalize_dates_in_db(conn)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return f"Error: {str(e)}"


def search_in_all_databases(query: str, **kwargs):
    """
    Busca en todas las BDs disponibles. Ignora filas donde todos
    los valores son None (p.ej. AVG sin coincidencias).
    """
    for db in ["b2c", "b2b", "general"]:
        res = issue_soql_query(query, db)
        if isinstance(res, list) and len(res) > 0:
            non_null = [row for row in res if any(v is not None for v in row.values())]
            if non_null:
                return non_null
    return []


def get_agents_with_max_cases(**kwargs):
    """Identifica a los 5 agentes (OwnerId) con mayor volumen de casos."""
    query = 'SELECT OwnerId, COUNT(Id) as total FROM "Case" GROUP BY OwnerId ORDER BY total DESC LIMIT 5'
    return search_in_all_databases(query)


def calculate_average_handle_time(priority: str = None, status: str = None, **kwargs):
    """
    Calcula el tiempo promedio de resolución en horas para casos cerrados.
    Usa TO_ISO() para normalizar fechas ISO 8601 (2021-06-07T10:50:00.000+0000).
    Acepta filtros opcionales: priority (ej: 'High') y status (ej: 'Closed').
    """
    filters = ['ClosedDate IS NOT NULL']

    if priority:
        filters.append(f"Priority = '{priority.strip(chr(39) + chr(34))}'")
    if status:
        filters.append(f"Status = '{status.strip(chr(39) + chr(34))}'")

    where_clause = " AND ".join(filters)
    query = (
        'SELECT '
        '  ROUND(AVG(JULIANDAY(TO_ISO(ClosedDate)) - JULIANDAY(TO_ISO(CreatedDate))) * 24, 2) AS avg_hours, '
        '  COUNT(*) AS total_cases '
        f'FROM "Case" WHERE {where_clause}'
    )

    result = search_in_all_databases(query)

    if not result:
        label = []
        if priority:
            label.append(f"Priority='{priority.strip(chr(39))}'")
        if status:
            label.append(f"Status='{status.strip(chr(39))}'")
        filter_desc = " y ".join(label) if label else "sin filtros"
        return [{"avg_hours": None, "total_cases": 0,
                 "mensaje": f"No se encontraron casos cerrados con {filter_desc}."}]

    return result

def generate_performance_report(**kwargs):
    """
    Genera un reporte detallado en Markdown sobre el desempeño de los agentes y KPIs de la DB.
    """
    agents = get_agents_with_max_cases()
    avg_time = calculate_average_handle_time(status='Closed')
    
    report = "# 📊 Reporte de Desempeño CRM Arena\n\n"
    report += f"**Tiempo Promedio de Resolución:** {avg_time[0].get('avg_hours', 'N/A')} horas\n"
    report += f"**Total de Casos Analizados:** {avg_time[0].get('total_cases', 0)}\n\n"
    report += "### 🏆 Top 5 Agentes (OwnerId)\n"
    
    for a in agents:
        report += f"- **ID:** `{a['OwnerId']}` | **Casos:** {a['total']}\n"
    
    return report