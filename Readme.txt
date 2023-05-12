------TicketShow------

TicketShow is a web application built using the Flask framework of Python that allows users to book tickets for various events happening around them. The application also has an admin interface where the admin can manage the venues and events. This Flask application also provides APIs for managing users, venues, and events. The application uses SQLAlchemy for database operations and Flask-Login for user authentication.

The APIs use request parsing and marshaling to validate and format data. The User and Admin/Organizer also require authentication, which is implemented using Flask-Login. Passwords are hashed using Werkzeug's generate_password_hash function.


----Features----
User and admin authentication
User can view all events
User can search the event according to the city
User can book tickets for the events
Admin can add, update and delete the venues
Admin can add, update and delete the events


----Installation----

To install the dependencies, run the following command in the terminal:
Copy code
pip install -r requirements.txt


To run the application, run the following command in the terminal:
Copy code
python app.py
Then open http://localhost:5000 in your browser to view the application.

----Dependencies----
Flask==2.0.1
Flask-Login==0.5.0
Flask-RESTful==0.3.9
Flask-SQLAlchemy
Werkzeug==2.0.1

The following APIs are provided:

User APIs:

GET /users - Get all users
GET /users/int:id - Get a user by id
POST /users - Create a new user
PUT /users/int:id - Update a user by id
DELETE /users/int:id - Delete a user by id

Venue APIs:

GET /venues - Get all venues
GET /venues/int:id - Get a venue by id
POST /venues - Create a new venue
PUT /venues/int:id - Update a venue by id
DELETE /venues/int:id - Delete a venue by id

Event APIs:

GET /events - Get all events
GET /events/int:id - Get an event by id
POST /events - Create a new event
PUT /events/int:id - Update an event by id
DELETE /events/int:id - Delete an event by id

