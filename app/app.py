# Import necessary libraries
import mysql.connector  # To connect to MySQL database
from flask import Flask, jsonify, request, make_response  # Flask for web framework and request/response handling
from datetime import datetime, timedelta  # For working with time (timestamp, expiration)
import socket  # To get internal server IP address
import time  # To add delays between retries
import logging

# Create Flask app instance
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MySQL database connection function with retry logic
def get_db_connection():
        try:
            # Attempt to connect to the MySQL database
            connection = mysql.connector.connect(
                host="db",  # Hostname where MySQL database is hosted
                user="root",  # Database username
                password="1234",  # Database password
                database="app_db"  # The database we are connecting to
            )
            return connection  # Return connection if successful
        except mysql.connector.Error as err:
            # Log error message if connection fails
            logging.error(f"Database connection failed: {err}")
            print(f"Database connection failed: {err}")
            return None

# Initialize global counter variable
global_counter = 0  # Start counter from 0

# Function to fetch the current value of the global counter from the database
def get_global_counter():
    conn = get_db_connection()  # Get a database connection
    if conn is None:  # If the connection failed, return None
        return None

    try:
        cursor = conn.cursor()  # Create a cursor to execute SQL queries
        cursor.execute("SELECT value FROM global_counter WHERE id = 1")  # Query to get the global counter
        result = cursor.fetchone()  # Fetch the result from the query
        if result:
            return result[0]  # Return the counter value if found
        else:
            return 0  # Return 0 if no record found for the counter
    except mysql.connector.Error as err:
        # Log error if there is an issue with the query
        print(f"Error fetching global counter: {err}")
        return None  # Return None if an error occurs
    finally:
        cursor.close()  # Close the cursor
        conn.close()  # Close the database connection

# Function to save the global counter value to the database
def save_global_counter(counter_value):
    conn = get_db_connection()  # Get a database connection
    if conn is None:  # If the connection failed, return False
        return False

    try:
        cursor = conn.cursor()  # Create a cursor to execute SQL queries
        # Insert or update the global counter in the database
        cursor.execute(
            "INSERT INTO global_counter (id, value) VALUES (1, %s) ON DUPLICATE KEY UPDATE value = %s",
            (counter_value, counter_value)  # Pass counter value for insertion or update
        )
        conn.commit()  # Commit the transaction
        return True  # Return True if the operation was successful
    except mysql.connector.Error as err:
        # Log error if there is an issue with the query
        print(f"Error saving global counter: {err}")
        return False  # Return False if an error occurs
    finally:
        cursor.close()  # Close the cursor
        conn.close()  # Close the database connection

# Route to increment the global counter and log access information
@app.route('/')
def increment_counter():
    global global_counter  # Access the global counter variable
    try:
        # Increment the global counter value
        global_counter += 1
        client_ip = request.remote_addr  # Get the client's IP address from the request
        internal_ip = socket.gethostbyname(socket.gethostname())  # Get the internal server IP address

        # Save access log to the database
        conn = get_db_connection()
        if conn is None:
            raise Exception("Database connection failed")

        cursor = conn.cursor()
        # Insert the access log into the access_log table
        cursor.execute(
            "INSERT INTO access_log (access_time, client_ip, internal_ip) VALUES (%s, %s, %s)",
            (datetime.now(), client_ip, internal_ip)  # Log the current time, client IP, and internal IP
        )
        conn.commit()  # Commit the transaction

        # Create a response with the internal IP address and the updated global counter
        resp = make_response(f"Internal IP address: {internal_ip}, Counter: {global_counter}")
        # Set a cookie with the internal IP address, valid for 5 minutesd
        resp.set_cookie('internal_ip', internal_ip, max_age=timedelta(minutes=5))
        return resp  # Return the response to the client

    except mysql.connector.Error as db_error:
        # Handle any database errors and log the error
        app.logger.error(f"Database error: {db_error}")
        return jsonify({"error": f"Database error: {db_error}"}), 500  # Return error response
    except Exception as e:
        # Handle other general errors
        app.logger.error(f"General error: {e}")
        return jsonify({"error": str(e)}), 500  # Return error response

# Route to display the current value of the global counter
@app.route('/showcount')
def show_count():
    # Get the current global counter from the database
    global_counter = get_global_counter()
    if global_counter is None:
        return jsonify({"error": "Failed to fetch global counter"}), 500  # Return error if fetch fails

    return jsonify({"global_counter": global_counter})  # Return the global counter as JSON response

# Main entry point to start the Flask app
if __name__ == "__main__":
    # Run the app on all available network interfaces on port 5000
    app.run(host="0.0.0.0", port=5000)
