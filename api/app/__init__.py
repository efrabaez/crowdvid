import os
from flask import Flask, render_template, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from dataclasses import dataclass


app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql+psycopg2://{user}:{passwd}@{host}:{port}/{table}".format(
    user=os.getenv("POSTGRES_USER"),
    passwd=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=5432,
    table=os.getenv("POSTGRES_DB"),
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class UserModel(db.Model):
    __tablename__ = "user"

    userId = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String())
    lastname = db.Column(db.String())
    email = db.Column(db.String())
    password = db.Column(db.String())
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)

    def __init__(self, name, lastname, email, password):
        self.name = name
        self.lastname = lastname
        self.email = email
        self.password = password

    def __repr__(self):
        return f"<User {self.email}>"

@dataclass
class PlaceModel(db.Model):
    __tablename__ = "place"
    
    placeId: int
    name: str

    placeId = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String())
    
    def __init__(self, name):
        self.name = name

class PlaceStatisticsModel(db.Model):
    __tablename__ = "statistics"

    statisticId = db.Column(db.Integer, primary_key = True, autoincrement = True)
    placeId = db.Column(db.Integer)
    ocupability = db.Column(db.Integer)

    def __init__(self, placeId, ocupability):
        self.placeId = placeId
        self.ocupability = ocupability

    def __repr__(self):
        return f"<Place {self.placeId}, Ocupability {self.ocupability}>"


@app.route('/')
def index():
    return render_template('index.html',
                           title = "Crowdvid",
                           url = os.getenv("URL"))

#User enpoints
@app.route('/api/users/register', methods = ('GET', 'POST'))
def user_register():
    if request.method == 'POST':
        name = request.json.get('name')
        lastname = request.json.get('lastname')
        email = request.json.get('email')
        password = request.json.get('password')
        error = None
        
        if not email:
            error = 'Email is required'
        elif not password:
            error = 'Password is required'
        elif UserModel.query.filter_by(email = email).first() is not None:
            error = f"Email {email} is already registered."
        
        if error is None:
            new_user = UserModel(name, lastname, email, generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            return jsonify(email = email,
                        code = 200,
                        message = f"User with email: {email} created successfully")
        else:        
            return jsonify(code = 418,
                       message = error)
        
    return "Register Page not yet implemented", 501


@app.route('/api/users/login', methods = ('GET', 'POST'))
def user_login():
    if request.method == 'POST':
        email = request.json.get('email')
        password = request.json.get('password')
        error = None
        user = UserModel.query.filter_by(email=email).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            return jsonify(userId = user.userId,
                        name = user.name,
                        lastname = user.lastname,
                        email = user.email,
                        created_at = user.created_at,
                        modified_at = user.modified_at,
                        code = 200,
                        message = "Login Successful")
        else:
            return jsonify(code = 418,
                       message = error)
    
    ## TODO: Return a login page
    return "Login Page not yet implemented", 501

#Place endpoints
@app.route('/api/places/register', methods=["POST"])
def place_register():
    name = request.json.get('place_name')
    error = None
    
    if not name:
        error = 'Place name is required'
    elif PlaceModel.query.filter_by(name = name).first() is not None:
        error = f"Place {name} is already registered."
    
    if error:
        return jsonify(code = 418,
                    message = error)
        
    new_place = PlaceModel(name)
    db.session.add(new_place)
    db.session.commit()
    return jsonify(place = name,
                    code = 200,
                    message = f"Place with name: {name} created successfully")

@app.route('/api/places/all',  methods=["GET"])
def place_all():
        error = None
        places = PlaceModel.query.all()
        

        if not places:
            error = 'There are no places registered.'

        if error:
            return jsonify(code= 418,
                            message=error)
            
        return jsonify(places = places,
            code = 200,
            message ="Success")
        
        
#Occupabilty per place
@app.route('/api/place/ocupability', methods=["POST"])
def statistics_place_register():
    placeId = request.json.get('place_id')
    ocupability = request.json.get('ocupability')
    error = None
    message = None 
    place = PlaceStatisticsModel.query.filter_by(placeId = placeId).first()
    
    if not placeId:
        error = 'Place id is required'
    elif place:
        place.ocupability = ocupability
        db.session.commit()
        message = f"Updated of statistics for place with id {placeId} was successfull"
    else:
        new_statistic = PlaceStatisticsModel(placeId, ocupability)
        db.session.add(new_statistic)
        db.session.commit()
        message = f"Creation of statistics for place with id {placeId} was successfull"
    if error:
        return jsonify(code = 418,
                    message = error)
        

    return jsonify(placeId = placeId,
                   ocupability=ocupability,
                    code = 200,
                    message = message)

@app.route('/api/place/ocupability/<placeId>',  methods=["GET"])
def statistics_place_get(placeId):      
        error = None
        place = PlaceStatisticsModel.query.filter_by(placeId = placeId).first()

        if not placeId:
            error = 'Place id required.'
        
        if place == None:
            error = f"Theres no place with id {placeId}"

        if error:
            return jsonify(code= 418,
                            message=error)
            
        return jsonify(id_place = place.placeId,
                ocupability = place.ocupability,
                code = 200,
                message ="Success")

@app.route('/health')
def health():
    return {'message': 'Healthy'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)