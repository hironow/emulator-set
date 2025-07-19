import asyncpg
import litellm


class DatabaseAgent:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string

    async def process_query(self, query: str) -> str:
        response = await litellm.acompletion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a SQL query generator. Convert natural language queries to SQL.",
                },
                {"role": "user", "content": query},
            ],
        )
        return response.choices[0].message.content

    async def execute_sql(self, sql: str) -> list:
        conn = await asyncpg.connect(self.connection_string)
        try:
            result = await conn.fetch(sql)
            return [dict(row) for row in result]
        finally:
            await conn.close()

    async def query(self, natural_language_query: str) -> list:
        sql = await self.process_query(natural_language_query)
        return await self.execute_sql(sql)
