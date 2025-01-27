# BP6 Non-Scan Project - Database Connection Class
# Author: Nina Schrauwen
import mysql.connector

class Database:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                port="8080",
                user="Admin",
                password="Brownie#99",
                database="netflix_titles"
            )
            self.cursor = self.connection.cursor()
            print("Connected to the database")
        except mysql.connector.Error as e:
            print(f"Error connecting to the database: {e}")
            exit(1)

    def validate_user(self, username, password):
        """
                Validates the user by workerID and password.
                Returns the worker's name if credentials are correct, otherwise None.
        """
        query = "SELECT workerName FROM jumboworkers WHERE workerID = %s AND password = %s"
        self.cursor.execute(query, (username, password))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return False

    def close_connection(self):
        """Closes the database connection."""
        self.connection.close()
        print("Database connection closed")
