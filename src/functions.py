import sqlite3
import os
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta

def issue_soql_query(query, sf_connector=None):
    """
    Executes a query against the local SQLite database instead of Salesforce Cloud.
    Maintains compatibility with the CRMArena benchmark logic.
    """
    try:
        # Construct path to the database within the container structure
        db_path = os.path.join("src", "local_data", "crmarena_data.db")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Execute query. Note: SQLite is compatible with basic SOQL syntax
        cursor.execute(query)
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    except Exception as e:
        return f"Local DB Error: {str(e)}"

def get_agents_with_max_cases(subset_cases, sf_connector=None):
    """
    Analyzes a subset of cases to find agents with the highest workload.
    """
    try:
        if not isinstance(subset_cases, list):
            return "Error: Input 'subset_cases' must be a list"

        agent_issue_counts = defaultdict(int)
        for record in subset_cases:
            owner_id = record.get('OwnerId')
            if owner_id:
                agent_issue_counts[owner_id] += 1
        
        if not agent_issue_counts:
            return []

        max_cases = max(agent_issue_counts.values())
        return [agent_id for agent_id, count in agent_issue_counts.items() if count == max_cases]
    except Exception as e:
        return f"Error: {str(e)}"

def calculate_average_handle_time(subset_cases, sf_connector=None):
    """
    Calculates the AHT (Average Handle Time) in minutes for a subset of closed cases.
    """
    try:
        if not subset_cases:
            return 0.0

        total_time = 0
        count = 0
        for case in subset_cases:
            created = case.get('CreatedDate')
            closed = case.get('ClosedDate')
            if created and closed:
                # Assuming standard ISO format from SQLite strings
                fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
                try:
                    start = datetime.strptime(created, fmt)
                    end = datetime.strptime(closed, fmt)
                    total_time += (end - start).total_seconds() / 60
                    count += 1
                except:
                    continue
        
        return total_time / count if count > 0 else 0.0
    except Exception as e:
        return f"Error calculating AHT: {str(e)}"

# Meta-information for tool-calling agents
issue_soql_query.__info__ = {
    "type": "function",
    "function": {
        "name": "issue_soql_query",
        "description": "Executes a query to retrieve data from the local Salesforce-mock database.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The SQL/SOQL query string."}
            },
            "required": ["query"]
        }
    }
}