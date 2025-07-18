import psycopg2
from psycopg2 import pool
import threading
import time
from typing import Union, List

# Local import
from .configs.config_cls import PostgreSQLConfig
from .configs.global_config import POSTGRES_CONFIG
from ..utils.logger import logger


class PostgreSQLConnectionPool:
    """
    A class to manage a PostgreSQL database connection pool and provide basic CRUD operations.
    """
    def __init__(self, config: PostgreSQLConfig = POSTGRES_CONFIG):
        """
        Initializes the PostgreSQL connection pool.

        Args:
            config (PostgreSQLConfig): The configuration for the PostgreSQL connection pool.
        """
        try:
            # Create a SimpleConnectionPool instance
            self.postgreSQL_pool = pool.SimpleConnectionPool(
                minconn=config.min_connections,
                maxconn=config.max_connections,
                dbname=config.dbname,
                user=config.user,
                password=config.pwd.get_secret_value(),
                host=config.host,
                port=config.port
            )
            logger.debug(f"PostgreSQL connection pool created successfully with min={config.min_connections}, max={config.max_connections} connections.")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Error while connecting to PostgreSQL: {error}")
            self.postgreSQL_pool = None # Set pool to None if initialization fails

    def get_connection(self):
        """
        Retrieves a database connection from the pool.

        Returns:
            psycopg2.connection or None: The connection object if successfully retrieved; otherwise, None.
        """
        if self.postgreSQL_pool:
            try:
                connection = self.postgreSQL_pool.getconn()
                return connection
            except (Exception, psycopg2.Error) as error:
                logger.error(f"Error while getting connection from pool: {error}")
                return None
        return None # Return None if the pool is not initialized

    def put_connection(self, connection):
        """
        Returns a database connection to the pool.

        Args:
            connection (psycopg2.connection): The connection object to return.
        """
        if self.postgreSQL_pool and connection:
            try:
                self.postgreSQL_pool.putconn(connection)
            except (Exception, psycopg2.Error) as error:
                logger.error(f"Error while returning connection to pool: {error}")

    def close_all_connections(self):
        """
        Closes all database connections in the pool.
        """
        if self.postgreSQL_pool:
            try:
                self.postgreSQL_pool.closeall()
                logger.debug("All connections in PostgreSQL pool are closed.")
            except (Exception, psycopg2.Error) as error:
                logger.error(f"Error while closing all connections: {error}")

    def _execute_query(self, sql_query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        Internal helper method to execute a SQL query and manage connection.

        Args:
            sql_query (str): The SQL query string.
            params (tuple or list, optional): Parameters for the SQL query. Defaults to None.
            fetch_one (bool): If True, fetches one row.
            fetch_all (bool): If True, fetches all rows.
            commit (bool): If True, commits the transaction.

        Returns:
            tuple or list or None: Fetched data, or None for DML operations.
        """
        conn = None
        result = None
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query, params)
                    if commit:
                        conn.commit()
                    if fetch_one:
                        result = cursor.fetchone()
                    elif fetch_all:
                        result = cursor.fetchall()
            else:
                logger.error("Failed to get a connection from the pool.")
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Error executing query: {sql_query} with params {params}. Error: {error}")
            if conn:
                conn.rollback() # Rollback in case of error
        finally:
            if conn:
                self.put_connection(conn)
        return result

    def insert_data(self, table_name: str, columns: list, values: tuple):
        """
        Inserts data into a specified table.

        Args:
            table_name (str): The name of the table.
            columns (list): A list of column names.
            values (tuple): A tuple to insert.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        if not table_name or not columns or not values:
            logger.error("Table name, columns, and values cannot be empty for insertion.")
            return False

        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(values))
        sql_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"
        
        logger.debug(f"Attempting to insert: {sql_query}, values: {values}")
        self._execute_query(sql_query, values, commit=True)
        logger.debug(f"Data inserted into {table_name}.")
        return True


    def bulk_insert_data(self, table_name: str, columns: list, values: List[tuple]):
        """
        Inserts multiple rows of data into a specified table.

        Args:
            table_name (str): The name of the table.
            columns (list): A list of column names.
            values (List[tuple]): A list of tuples to insert.

        Returns:
            bool: True if bulk insertion was successful, False otherwise.
        """
        if not table_name or not columns or not values:
            logger.error("Table name, columns, and values cannot be empty for bulk insertion.")
            return False

        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        sql_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"
        
        logger.debug(f"Attempting to bulk insert: {sql_query}, values: {len(values)} rows")
        
        conn = None
        try:
            conn = self.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.executemany(sql_query, values)
                    conn.commit()
                    logger.debug(f"Bulk data inserted into {table_name}.")
                    return True
            else:
                logger.error("Failed to get a connection from the pool.")
                return False
        except (Exception, psycopg2.Error) as error:
            logger.error(f"Error executing bulk insert query: {sql_query} with {len(values)} rows. Error: {error}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.put_connection(conn)


    def select_data(self, table_name, columns="*", conditions=None, params=None, fetch_one=False):
        """
        Selects data from a specified table.

        Args:
            table_name (str): The name of the table.
            columns (str or list): Columns to select. Defaults to "*".
            conditions (str, optional): SQL WHERE clause conditions. Defaults to None.
            params (tuple or list, optional): Parameters for the conditions. Defaults to None.
            fetch_one (bool): If True, fetches only one row. Defaults to False.

        Returns:
            list of tuples or tuple or None: Fetched data.
        """
        if not table_name:
            logger.error("Table name cannot be empty for selection.")
            return None

        if isinstance(columns, list):
            columns_str = ", ".join(columns)
        else:
            columns_str = columns

        sql_query = f"SELECT {columns_str} FROM {table_name}"
        if conditions:
            sql_query += f" WHERE {conditions}"
        sql_query += ";"

        logger.debug(f"Attempting to select: {sql_query}, params: {params}")
        if fetch_one:
            return self._execute_query(sql_query, params, fetch_one=True)
        else:
            return self._execute_query(sql_query, params, fetch_all=True)

    def update_data(self, table_name, set_clause, conditions, params):
        """
        Updates data in a specified table.

        Args:
            table_name (str): The name of the table.
            set_clause (str): The SET clause (e.g., "column1 = %s, column2 = %s").
            conditions (str): The WHERE clause conditions.
            params (tuple or list): Parameters for the SET clause and WHERE clause.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not table_name or not set_clause or not conditions or not params:
            logger.error("Table name, set clause, conditions, and parameters cannot be empty for update.")
            return False

        sql_query = f"UPDATE {table_name} SET {set_clause} WHERE {conditions};"
        
        logger.debug(f"Attempting to update: {sql_query}, params: {params}")
        self._execute_query(sql_query, params, commit=True)
        logger.debug(f"Data updated in {table_name}.")
        return True

    def delete_data(self, table_name, conditions, params):
        """
        Deletes data from a specified table.

        Args:
            table_name (str): The name of the table.
            conditions (str): The WHERE clause conditions.
            params (tuple or list): Parameters for the WHERE clause.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if not table_name or not conditions or not params:
            logger.error("Table name, conditions, and parameters cannot be empty for deletion.")
            return False

        sql_query = f"DELETE FROM {table_name} WHERE {conditions};"
        
        logger.debug(f"Attempting to delete: {sql_query}, params: {params}")
        self._execute_query(sql_query, params, commit=True)
        logger.debug(f"Data deleted from {table_name}.")
        return True

    def upsert_data(self, table_name: str, columns: list, values: tuple, conflict_target: Union[str, List[str]], update_columns: List[str]):
        """
        Inserts or updates data into a specified table using ON CONFLICT (UPSERT).

        Args:
            table_name (str): The name of the table.
            columns (list): A list of column names for the INSERT part.
            values (tuple): A tuple of values for the INSERT part.
            conflict_target (Union[str, List[str]]): The column(s) that define the unique constraint
                                                     causing the conflict (e.g., "email" or ["first_name", "last_name"]).
            update_columns (List[str]): A list of columns to update if a conflict occurs.
                                       These columns will be updated to their EXCLUDED (new) values.

        Returns:
            bool: True if upsert was successful, False otherwise.
        """
        if not table_name or not columns or not values or not conflict_target or not update_columns:
            logger.error("Table name, columns, values, conflict_target, and update_columns cannot be empty for upsert.")
            return False

        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(values))

        # Format conflict_target correctly
        if isinstance(conflict_target, list):
            conflict_target_str = "(" + ", ".join(conflict_target) + ")"
        else:
            conflict_target_str = f"({conflict_target})"

        # Construct the SET clause for ON CONFLICT DO UPDATE
        set_clause_parts = [f"{col} = EXCLUDED.{col}" for col in update_columns]
        set_clause = ", ".join(set_clause_parts)

        sql_query = f"""
        INSERT INTO {table_name} ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT {conflict_target_str} DO UPDATE SET {set_clause};
        """
        
        logger.debug(f"Attempting to upsert: {sql_query}, values: {values}")
        self._execute_query(sql_query, values, commit=True)
        logger.debug(f"Data upserted into {table_name}.")
        return True


POSTGRES_POOL = PostgreSQLConnectionPool()

