from typing import Any, Dict
from .agent import CustomAgent


class CustomAgentSkill:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.agent = CustomAgent(connection_string)

    async def execute(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query")
        if not query:
            raise ValueError("No query provided in input_data")

        sql = await self.agent.process_query(query)
        results = await self.agent.execute_sql(sql)

        return {"natural_language_query": query, "sql": sql, "results": results}
