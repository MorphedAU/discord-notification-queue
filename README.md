# Discord Notification Queue
There have been a few times that I have had my Internet go down (yay Australian internet!) and I have missed some notifications that are being pushed to discord by various services of mine which fire and forget.

This script solves that issue without having to fully customize a script for each service by receiving the notifications itself, and using an SQLite database to store them if it is unable to reach the Discord API. The services can then be updated to use this endpoint.

Made public as I figured this may help someone else.

Disclaimer: It started as a ChatGPT prompt, and then modified fairly heavily by myself.

> [!WARNING]
> This endpoint has no authentication. If made public and someone knows what you have named your webhook, it could be abused to spam the channel.

## Requirements
Python 3 (Tested on 3.11.2)  
Python 3 venv

## Installing  
  
Install python3 and python3-venv  
```sudo apt install python3 python3-venv```  

Make a directory for the application, and change to it.

Pull the application to the current directory  
``` git clone https://github.com/MorphedAU/discord-notification-queue.git . ```

Create the python venv  
`python3 -m venv ./.venv`  

Activate the venv  
`source ./.venv/bin/activate`  
  
Install Python dependencies:  
`pip install -r requirements.txt`  

Copy .env-example to .env and .webhooks-example to .webhooks and modify as required.

Run the application:  
`python app.py`

## Testing the application 
Use the below curl command to test the application, swapping in your own details as required (webhook_name and IP)  
```
curl -X POST -d  '{ 
   "webhook_name": "webhook1",
   "title": "Test Post",
   "content": "This is a test post, from the discord notification queue!",
   "username": "Discord Notification Queue"
   }'
   -H 'Content-Type: application/json' \
   http://127.0.0.1:5000/notify
```

## Making app a service

Update the path in discord-queue.service using where you have installed the application.  
Copy discord-queue.service into `/etc/systemd/system`  

Reload systemd daemon  
`sudo systemctl daemon-reload`  

Start the service  
`sudo systemctl start discord-queue`

Enable service  
`sudo systemctl enable discord-queue`