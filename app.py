from flask import Flask, request, jsonify
import mysql.connector
import os
from dotenv import load_dotenv
import requests
import threading
import time

load_dotenv()

app = Flask(__name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB")
    )

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
        "INSERT INTO notifications (webhook_name, title, content, username) VALUES (%s, %s, %s, %s)",
        (webhook_name, title, content, username)
    )
    db.commit()
    cursor.close()
    db.close()
    return jsonify({'status': 'Notification queued'}), 200

def process_queue():
    while True:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

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
                response.raise_for_status()  # Raise an error for bad status codes

                if response.status_code in [201, 204]:
                    cursor.execute(
                        "INSERT INTO archived_notifications (webhook_name, title, content, username) VALUES (%s, %s, %s, %s)",
                        (notification['webhook_name'], notification['title'], notification['content'], notification['username'])
                    )
                    cursor.execute("DELETE FROM notifications WHERE id = %s", (notification['id'],))
                elif response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get("Retry-After", 5))
                    print(f"Rate limited. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)
                else:
                    cursor.execute(
                        "INSERT INTO failed_notifications (webhook_name, title, content, username, error) VALUES (%s, %s, %s, %s, %s)",
                        (notification['webhook_name'], notification['title'], notification['content'], notification['username'], response.text)
                    )
                    cursor.execute("DELETE FROM notifications WHERE id = %s", (notification['id'],))

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                # Log the exception or take necessary action
                # Leave the notification in the queue for retry

            db.commit()

        cursor.close()
        db.close()

        time.sleep(5)  # Adjust the sleep time as needed

if __name__ == '__main__':
    if os.getenv("FLASK_ENV") != "development":  # Check if the script is not running in development mode
        queue_thread = threading.Thread(target=process_queue)
        queue_thread.start()
    app.run(host='0.0.0.0', debug=os.getenv("FLASK_ENV") == "development")
