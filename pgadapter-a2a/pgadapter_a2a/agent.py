import asyncpg
import litellm
import logging
from dotenv import load_dotenv

load_dotenv()


class DatabaseAgent:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def process_query(self, query: str) -> str:
        self.logger.info(f"Processing natural language query: {query}")
        try:
            self.logger.debug("Calling LLM for SQL generation")
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
            sql = response.choices[0].message.content
            self.logger.info(f"Generated SQL: {sql}")
            return sql
        except Exception as e:
            self.logger.error(f"LLM query generation failed: {e}")
            raise

    async def execute_sql(self, sql: str) -> list:
        self.logger.info(f"Executing SQL query: {sql}")
        self.logger.debug(f"Connecting to database: {self.connection_string}")

        conn = await asyncpg.connect(self.connection_string)
        try:
            result = await conn.fetch(sql)
            rows = [dict(row) for row in result]
            self.logger.info(f"Query executed successfully, {len(rows)} rows returned")
            self.logger.debug(
                f"First few results: {rows[:3] if rows else 'No results'}"
            )
            return rows
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            raise
        finally:
            await conn.close()
            self.logger.debug("Database connection closed")

    async def query(self, natural_language_query: str) -> list:
        self.logger.info(f"Processing end-to-end query: {natural_language_query}")
        sql = await self.process_query(natural_language_query)
        return await self.execute_sql(sql)
