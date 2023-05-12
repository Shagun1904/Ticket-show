from flask import Flask, render_template, redirect, request, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user, current_user
from flask_restful import Api, Resource, abort, reqparse, fields, marshal_with


#------- Flask App Configuration --------
app=Flask(__name__)
app.config['SECRET_KEY']='thisismysecretkey'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///TicketShow.sqlite'
db=SQLAlchemy()
db.init_app(app)
api=Api(app)
app.app_context().push()



#------- LoginManager Configuration -------
login_manager= LoginManager()
login_manager.session_protection= 'strong'
login_manager.login_view= 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)






#----------- Databases for TicketShow --------

#User Database
class Users(UserMixin, db.Model):
    __tablename__='users'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    userType=db.Column(db.String(100), nullable=False)
    email=db.Column(db.String(100), unique=True, nullable=False)
    name=db.Column(db.String(50), nullable=False)
    password=db.Column(db.String(200), nullable=False)
    venue=db.relationship('Venue', backref='users')
    booking=db.relationship('Booking', backref='users')



#Venue Database
class Venue(UserMixin, db.Model):
    __tablename__='venues'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    v_venueName=db.Column(db.String(200), unique=True, nullable=False)
    v_place=db.Column(db.String(60), nullable=False)
    v_location=db.Column(db.String(60), nullable=False)
    v_capacity=db.Column(db.Integer, nullable=False)
    v_organizer=db.Column(db.String(60), nullable=False)
    admin_id=db.Column(db.Integer, db.ForeignKey('users.id'))
    event=db.relationship('Event', backref='venues')
    booking=db.relationship('Booking', backref='venues')


#Event Database
class Event(UserMixin, db.Model):
    __tablename__='events'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    e_title=db.Column(db.String(200), unique=True, nullable=False)
    e_time=db.Column(db.String(50), nullable=False)
    e_tags=db.Column(db.String(400))
    e_price=db.Column(db.Integer, nullable=False)
    e_location=db.Column(db.String(60), nullable=False)
    e_venue=db.Column(db.String(60), nullable=False)
    venue_id=db.Column(db.Integer, db.ForeignKey('venues.id'))
    booking=db.relationship('Booking', backref='events')


#Booking Database
class Booking(UserMixin, db.Model):
    __tablename__='booking'
    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    b_name=db.Column(db.String(100), nullable=False)
    b_email=db.Column(db.String(100), nullable=False)
    b_eventName=db.Column(db.String(200), nullable=False)
    b_price=db.Column(db.Integer, nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id=db.Column(db.Integer, db.ForeignKey('events.id'))
    venue_id=db.Column(db.Integer, db.ForeignKey('venues.id'))


#---------- Routes for TicketShow --------

#---- Non-Auth Routes ----

#Login process for user/admin
@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method=='GET':
        return render_template("login.html")
    else:
        #Getting input from form
        Password=request.form["passwordLogin"]
        Email=request.form["emailLogin"]
        
        #Searching in User Database for the user
        user=Users.query.filter_by(email=Email).first()

        #Checking if user exist or not
        if not user or not check_password_hash(user.password, Password):
            flash('Please check your login credentials and try again.')
            return redirect(url_for('login'))
        
        else:
            #Check the userType of user and redirecting accordingly
            if user.userType=='user':
                login_user(user)
                flash('Logged in successfully')
                return redirect(url_for('home'))
            else:
                login_user(user)
                flash('Logged in successfully')
                return redirect(url_for('adminHome'))

#Sign up process for user/admin
@app.route('/signup', methods=["POST","GET"])
def signup():
    if request.method=="GET":
        return render_template("signup.html")
    else:
        #Getting input from form
        UserType=request.form["userType"]
        Name=request.form["nameSignup"]
        Email=request.form["emailSignup"]
        Password=request.form["passwordSignup"]

        #Searching in User Database
        user=Users.query.filter_by(email=Email).first()

        #Checking if user exits or not
        if user:
            flash('User Email already exists')
            return redirect(url_for('signup'))
        
        #Adding new user to the User Database
        new_user=Users(userType=UserType,email=Email,name=Name,password=generate_password_hash(Password,method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))


#---- Auth routes ----

#User homepage
@app.route('/home', methods=["POST","GET"])
@login_required
def home():
    if request.method=="GET":
        #Getting all the registered events from querying the Event Database
        events=Event.query.all()
        return render_template('userhome.html', name=current_user.name,email=current_user.email,e_d=events)
    else:
        #Getting the input from form
        location = request.form['location']

        #Searching in Event Database
        events = Event.query.filter_by(e_location=location).all()

        #Checking if event already registered
        if not events:
            flash('No Events Registered yet. Select another location')
            return redirect(url_for('home'))
        
        return render_template('userhome.html', name=current_user.name,email=current_user.email,e_d=events)

#Admin homepage -- Rendering venues
@app.route('/adminhome', methods=["POST","GET"])
@login_required
def adminHome():
    if request.method=="GET":
        #Getting all the registered venues from querying the Venue Database
        venues=Venue.query.filter_by(v_organizer=current_user.email).all()
        return render_template('adminhome.html', name=current_user.name,email=current_user.email, v_d=venues)

#Logout    
@app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('login'))

#Creating venue
@app.route('/addvenue', methods=["POST","GET"])
@login_required
def createvenue():
    if request.method=="POST":
        #Getting input from form
        venueName=request.form["venueName"]
        place=request.form["place"]
        location=request.form["vLocation"]
        capacity=request.form["capacity"]
        organizer=current_user.email
        adminId=current_user.id

        #Searching in Venue Database
        venue=Venue.query.filter_by(v_venueName=venueName).first()

        #Checking if venue exists or not
        if venue:
            flash('Venue already register')
            return redirect(url_for('createvenue'))

        #Adding new venue to Venue Database
        v=Venue(v_venueName=venueName, v_place=place, v_location=location, v_capacity=capacity, v_organizer=organizer, admin_id=adminId)
        db.session.add(v)
        db.session.commit()
        flash('Venue Successfully Created')
        return redirect(url_for('adminHome'))
    else:
        return render_template('createVenues.html', name=current_user.name,email=current_user.email)

#Creating event and Rendering events
@app.route('/createvent/<int:id>', methods=["POST","GET"])
@login_required
def createvent(id):
    if request.method=="POST":
        #Getting inputs from form
        title=request.form["title"]
        time=request.form["time"]
        tags=request.form["tags"]
        eventVenue=request.form["eVenue"]
        eventLocation=request.form["eLocation"]
        price=request.form["price"]
        venueId=id

        #Searching in Event Database
        event=Event.query.filter_by(e_title=title).first()

        #Checking if event exists or not
        if event:
            flash('Event already Exists')
            return redirect(url_for('adminHome'))
        
        #Adding new event to Event Database
        c=Event(e_title=title, e_time=time, e_tags=tags, e_price=price, e_venue=eventVenue, e_location=eventLocation, venue_id=venueId)
        db.session.add(c)
        db.session.commit()
        flash('Event Created Successfully')
        return redirect(url_for('createvent', id=venueId))
    else:
        #Getting all the events by querying the Event Database
        v=Venue.query.get(id)
        events=Event.query.filter_by(venue_id=id).all()
        return render_template("createEvents.html", name=current_user.name,email=current_user.email,venueName=v.v_venueName, vLocation=v.v_location, e_d=events)

#Updating the venue
@app.route('/venueUpdate/<int:vid>',methods=["POST","GET"])
@login_required
def updateVenue(vid):
    if request.method == "GET":
        #Getting data from Venue Database and populating
        data = Venue.query.filter_by(id=vid).first()
        return render_template("updateVenue.html", v_id=data, name=current_user.name,email=current_user.email)
    else:
        #Creating a new object of Venue and committing 
        new= Venue.query.filter_by(id=vid).first()

        new.v_venueName=request.form["updateName"]
        new.v_place=request.form["updatePlace"]
        new.v_capacity=request.form["updateCapacity"]

        db.session.commit()
        return redirect(url_for('adminHome'))

#Deleting the venue    
@app.route('/venueDelete/<int:vid>' ,methods=["POST","GET"])
@login_required
def venueDelete(vid):
    #Searching the Venue Database by provided id and deleting it
    data=Venue.query.filter_by(id = vid).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(url_for('adminHome'))

#Updating the event
@app.route('/eventUpdate/<int:eid>',methods=["POST","GET"])
@login_required
def updateEvent(eid):
    if request.method == "GET":
        #Searching the Event Database and populating
        data = Event.query.filter_by(id=eid).first()
        return render_template("updateEvent.html", e_id=data, name=current_user.name,email=current_user.email)
    else:
        #Creating a new object of Event and committing
        new= Event.query.filter_by(id=eid).first()

        new.e_time=request.form["updateTime"]
        new.e_tags=request.form["updateTags"]
        new.e_price=request.form["updatePrice"]

        db.session.commit()
        return redirect(url_for('adminHome'))

#Deleting the event
@app.route('/eventDelete/<int:eid>' ,methods=["POST","GET"])
@login_required
def eventDelete(eid):
    #Searching the Event Database by provided id and deleting it
    data=Event.query.filter_by(id = eid).first()
    db.session.delete(data)
    db.session.commit()
    return redirect(url_for('adminHome'))

#Booking an event
@app.route('/book/<int:bid>', methods=["GET", "POST"])
@login_required
def book(bid):
    if request.method == 'GET':
        #Getting the event by querying the Database by provided id
        event = Event.query.get(bid)
        return render_template('book.html', e_d=event,name=current_user.name,email=current_user.email)
    else:
        #Getting the input form form
        noOfTickets = request.form['count']

        #Searching the event in Event Database
        event = Event.query.get(bid)
        
        #Calculating the totalPrice
        totalPrice = int(event.e_price)*int(noOfTickets)

        #Adding new booking to Booking Database
        new_booking=Booking(b_name=current_user.name, b_email=current_user.email, b_eventName=event.e_title,b_price=totalPrice,user_id=current_user.id, venue_id=event.venue_id,event_id=bid)
        db.session.add(new_booking)
        db.session.commit()

        flash('Booking Successful')
        return render_template('successBooking.html',name=current_user.name,email=current_user.email,tPrice=totalPrice)

#View all bookings
@app.route('/allBookings', methods=["POST","GET"])
@login_required
def bookings():
    if request.method=="GET":
        #Searching the Booking Database for all the bookings
        booking=Booking.query.filter_by(user_id=current_user.id).all()
        return render_template('allBookings.html',name=current_user.name,email=current_user.email, b_d=booking)

# ------------------------------------------------ APIs ---------------------------------------


#------- User APIs --------

user_field={
    'id': fields.Integer,
    'userType': fields.String,
    'email': fields.String,
    'name': fields.String,
    'password': fields.String
}

user_req=reqparse.RequestParser()
user_req.add_argument("userType")
user_req.add_argument("email")
user_req.add_argument("name")
user_req.add_argument("password")

update_user_req=reqparse.RequestParser()
update_user_req.add_argument("userType")
update_user_req.add_argument("email")
update_user_req.add_argument("name")
update_user_req.add_argument("password")

class UsersAPI(Resource):
    @marshal_with(user_field)
    def get(self, id=None):
        if id:
            user= Users.query.get(id)
            if not user:
                abort(404, message="user does not exist")
            else:    
                return user
        else:
            user =Users.query.all()
            return user, 200

    @marshal_with(user_field)
    def post(self, id=None):
        data= user_req.parse_args()
        p = generate_password_hash(data.password)
        if '@' not in data.email:
            abort(400, message="Invalid Email")
        if len(data.password) < 8:
            abort(400, message="password length is less than 8")
        user= Users(userType=data.userType,email=data.email,name=data.name,password=p)
        db.session.add(user)
        db.session.commit()
        return user,200
    
    @marshal_with(user_field)
    def put(self, id=None):
        if not id:
            abort(400, message="id Not Given")
        else:
            data= update_user_req.parse_args()
            user= Users.query.filter_by(id=id)
            if not user.first():
                abort(404, message="User Not Exist")
            else:
                data.password=generate_password_hash(data.password)
                user.update(data)
                db.session.commit()
                return user,200
    
    @marshal_with(user_field)
    def delete(self, id=None):
        if id:
            user=Users.query.get(id)
            if not user:
                abort(404,message="user does not exist")
            db.session.delete(user)
            db.session.commit()
            return "User successfully deleted.", 200
        else:
            abort(400, message="Enter User Id")



# ------- Venue APIs --------

venue_field={
    'id': fields.Integer,
    'v_venueName': fields.String,
    'v_place': fields.String,
    'v_location': fields.String,
    'v_capacity': fields.String,
    'v_organizer': fields.String,
    'admin_id': fields.Integer
}

venue_req=reqparse.RequestParser()
venue_req.add_argument("v_venueName")
venue_req.add_argument("v_place")
venue_req.add_argument("v_location")
venue_req.add_argument("v_capacity")
venue_req.add_argument("v_organizer")
venue_req.add_argument("admin_id")


update_venue_req=reqparse.RequestParser()
update_venue_req.add_argument("v_venueName")
update_venue_req.add_argument("v_place")
update_venue_req.add_argument("v_location")
update_venue_req.add_argument("v_capacity")
update_venue_req.add_argument("v_organizer")
update_venue_req.add_argument("admin_id")

class VenueAPI(Resource):
    @marshal_with(venue_field)
    def get(self, id=None):
        if id:
            venue= Venue.query.get(id)
            if not venue:
                abort(404, message="venue does not exist")
            else:    
                return venue, 200
        else:
            venue =Venue.query.all()
            return venue, 200

    @marshal_with(venue_field)
    def post(self, id=None):
        data= venue_req.parse_args()
        venue= Venue(v_venueName=data.v_venueName,v_place=data.v_place,v_location=data.v_location,v_capacity=data.v_capacity,v_organizer=data.v_organizer, admin_id=data.admin_id)
        db.session.add(venue)
        db.session.commit()
        return venue, 200
    
    @marshal_with(venue_field)
    def put(self, id=None):
        if not id:
            abort(400, message="id Not Given")
        else:
            data= update_venue_req.parse_args()
            venue= Venue.query.filter_by(id=id)
            if not venue.first():
                abort(404, message="venue Not Exist")
            else:
                venue.update(data)
                db.session.commit()
                return venue, 200
    
    @marshal_with(venue_field)
    def delete(self, id=None):
        if id:
            venue=Venue.query.get(id)
            if not venue:
                abort(404,message="venue does not exist")
            db.session.delete(venue)
            db.session.commit()
            return "Venue successfully deleted", 200
        else:
            abort(400, message="Enter venue Id")



#------- Event APIs -----


event_field={
    'id': fields.Integer,
    'e_title': fields.String,
    'e_time': fields.String,
    'e_tags': fields.String,
    'e_price': fields.String,
    'e_location': fields.String,
    'e_venue': fields.String,
    'venue_id': fields.Integer
}

event_req=reqparse.RequestParser()
event_req.add_argument("e_title")
event_req.add_argument("e_time")
event_req.add_argument("e_tags")
event_req.add_argument("e_price")
event_req.add_argument("e_location")
event_req.add_argument("e_venue")
event_req.add_argument("venue_id")


update_event_req=reqparse.RequestParser()
update_event_req.add_argument("e_title")
update_event_req.add_argument("e_time")
update_event_req.add_argument("e_tags")
update_event_req.add_argument("e_price")
update_event_req.add_argument("e_location")
update_event_req.add_argument("e_venue")
update_event_req.add_argument("venue_id")

class EventAPI(Resource):
    @marshal_with(event_field)
    def get(self, id=None):
        if id:
            event=Event.query.get(id)
            if not event:
                abort(404, message="Event does not exists")
            else:
                return event, 200
        else:
            event=Event.query.all()
            return event, 200      

    @marshal_with(event_field)
    def post(self, id=None):
        data= event_req.parse_args()
        event= Event(e_title=data.e_title,e_time=data.e_time,e_tags=data.e_tags,e_price=data.e_price,e_location=data.e_location,e_venue=data.e_venue,venue_id=data.venue_id)
        db.session.add(event)
        db.session.commit()
        return event, 200

    @marshal_with(event_field)
    def put(self, id=None):
        if not id:
            abort(400, message="id Not Given")
        else:
            data= update_event_req.parse_args()
            event= Event.query.filter_by(id=id)
            if not event.first():
                abort(404, message="event Not Exist")
            else:
                event.update(data)
                db.session.commit()
                return event, 200
            
    @marshal_with(event_field)
    def delete(self, id=None):
        if id:
            event=Event.query.get(id)
            if not event:
                abort(404,message="event does not exist")
            db.session.delete(event)
            db.session.commit()
            return "Event successfully deleted.", 200
        else:
            abort(400, message="Enter event Id")



api.add_resource(UsersAPI, '/api/users', '/api/users/<int:id>')
api.add_resource(VenueAPI, '/api/venues', '/api/venues/<int:id>')
api.add_resource(EventAPI, '/api/events', '/api/events/<int:id>')


if __name__=='__main__':
    db.create_all()
    app.run(debug=True)

