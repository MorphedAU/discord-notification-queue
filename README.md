Create a database and a user.

CREATE USER 'discordNotification'@'%' IDENTIFIED BY 'testPass';
GRANT ALL PRIVILEGES ON discordNotifcation.* To 'discordNotification'@'%';

Use the schema.sql to create the schema in the database



Running the service.
  
Install dependencies:  
pip install -r requirements.txt  
  
Run the application:  
python app.py