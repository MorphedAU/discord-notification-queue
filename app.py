from flask import Flask, request, jsonify
import sqlite3
import os
import json
from dotenv import load_dotenv
import requests
import threading
import time

load_dotenv()

app = Flask(__name__)

# Database connection
def get_db_connection():
    try:
        conn = sqlite3.connect(os.getenv("SQLITE_DB"))
        return conn
    except sqlite3.Error as e:
        print(e)

# Check DB Schema Inplace
def check_db_schema():
    conn = get_db_connection()
    query = """SELECT name FROM sqlite_master WHERE type='table';"""
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()

    if len(result) == 0:
        conn.close()
        return 0
    if len(result) != 3 and len(result) != 4:
        print('Database has too many tables. Closing')
        exit(1)
    
    tables = []
    for i in result:
        tables.append(i[0])
    tables.sort()

    if (tables[0] != 'archived_notifications' and
        tables[1] != 'failed_notifications' and
        tables[2] != 'notifications'): 
        print('Database tables do not match schema. Exiting')
        exit(2)

    conn.close()
    return 1

# Create DB Schema
def create_db_schema():
    conn = get_db_connection()
    f = open('schema.sql', 'r')
    query = f.read()
    f.close()

    cursor = conn.cursor()
    cursor.executescript(query)

    conn.close()

# Load webhooks
def load_webhooks():
    webhooks = {}
    with open('.webhooks', 'r') as file:
        for line in file:
            name, url = line.strip().split('=')
            webhooks[name] = url
    return webhooks

webhooks = load_webhooks()

# Endpoint to receive notifications
@app.route('/notify', methods=['POST'])
def notify():
    data = request.get_json()
    webhook_name = data.get('webhook_name')
    title = data.get('title')
    content = data.get('content')
    username = data.get('username', None)  # Optional bot name

    if webhook_name not in webhooks:
        return jsonify({'error': 'Invalid webhook name'}), 400

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO notifications (webhook_name, title, content, username) VALUES (?, ?, ?, ?)",
        (webhook_name, title, content, username)
    )
    db.commit()
    cursor.close()
    db.close()
    return jsonify({'status': 'Notification queued'}), 200

def process_queue():
    while True:
        try:
            db = get_db_connection()
            db.row_factory = sqlite3.Row

            cursor = db.cursor()

            cursor.execute("SELECT * FROM notifications LIMIT 1")
            notification = cursor.fetchone()

            if notification:
                webhook_url = webhooks[notification['webhook_name']]
                payload = {
                    'content': f"**{notification['title']}**\n{notification['content']}"
                }
                if notification['username']:
                    payload['username'] = notification['username']

                try:
                    response = requests.post(webhook_url, json=payload, timeout=15)
                    #response.raise_for_status()  # Raise an error for bad status codes

                    if response.status_code in [201, 204]:
                        cursor.execute(
                            "INSERT INTO archived_notifications (webhook_name, title, content, username) VALUES (?, ?, ?, ?)",
                            (notification['webhook_name'], notification['title'], notification['content'], notification['username'])
                        )
                        cursor.execute("DELETE FROM notifications WHERE id = ?", (notification['id'],))
                    elif response.status_code == 429:  # Rate limit
                        retry_after = int(response.headers.get("Retry-After", 5))
                        print(f"Rate limited. Retrying after {retry_after} seconds.")
                        time.sleep(retry_after)
                    else:
                        err = json.loads(response.text)
                        err['status_code'] = response.status_code
                        err = json.dumps(err)
                        cursor.execute(
                            "INSERT INTO failed_notifications (webhook_name, title, content, username, error) VALUES (?, ?, ?, ?, ?)",
                            (notification['webhook_name'], notification['title'], notification['content'], notification['username'], err)
                        )
                        cursor.execute(" DELETE FROM notifications WHERE id= ?;", (notification['id'],))

                    db.commit()

                except requests.exceptions.RequestException as e:
                    print(f"Request failed: {e}")
                    pass
                    # Log the exception or take necessary action
                    # Leave the notification in the queue for retry


            cursor.close()
            db.close()

            time.sleep(5)  # Adjust the sleep time as needed
        except:
            pass

if __name__ == '__main__':
    #check if database schema is in place, create if not exist
    if (check_db_schema() == 0):
        create_db_schema()
    if os.getenv("FLASK_ENV") != "development":  # Check if the script is not running in development mode
        queue_thread = threading.Thread(target=process_queue)
        queue_thread.daemon = True
        queue_thread.start()
    app.run(host='0.0.0.0', debug=os.getenv("FLASK_ENV") == "development")
