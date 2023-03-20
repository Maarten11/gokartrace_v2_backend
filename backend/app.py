from flask import Request, make_response, Flask
from flask_restful import Resource, Api

from sqlalchemy import create_engine, MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from werkzeug.middleware.dispatcher import DispatcherMiddleware

from models import THREADS, init_default_user, new_lap
from auth import Login, AuthCheck
from race_logic import CountRound, Teams, TeamView, Status

# from os import environ

# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# create the api
api = Api(app)
cors = CORS(app, supports_credentials=True, origins=["http://localhost:*", "https://gokartrace.ask-stuwer.be:*", "http://127.0.0.1:*", "http://192.168.0.207:*"])

# # Extract info from env
# postgres_user = environ["DB_USER"]
# postgres_password = environ["DB_PASSWORD"]
# postgres_db = environ["DB"]
# postgres_port = environ["DB_PORT"]

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:secure_password@db:5432/ds_2"
# app.config["CORS_HEADERS"] = 'Content-Type'
# initialize the app with the extension
db.init_app(app)

def simple(env, resp):
    resp(b'200 OK', [(b'Content-Type', b'text/plain')])
    return [b'use /api for the api']


app.wsgi_app = DispatcherMiddleware(simple, {'/api': app.wsgi_app})

# TODO: this is dangerous, remove
# engine = create_engine(
#     f"postgresql://{postgres_user}:{postgres_password}@db:{postgres_port}/{postgres_db}", pool_size=THREADS)

# Base.metadata.create_all(engine)

init_default_user()

class HelloWorld(Resource):
    def get(self):
        print("Calling init default user", flush=True)
        init_default_user()
        print("Initted default user", flush=True)
        return "Hello World"


class Test(Resource):
    def get(self):
        return "Get"
        return engine.table_names()


class AddRacer(Resource):
    def get(self):
        request = Request.args
        print(request, flush=True)
        return "AAA"
        db.session.execute()

class Lap(Resource):
    def get(self, team):
        new_lap(team)



api.add_resource(HelloWorld, "/")
api.add_resource(AddRacer, "/add")
api.add_resource(Login, Login.route())
api.add_resource(CountRound, CountRound.route())
api.add_resource(Teams, Teams.route())
api.add_resource(TeamView, TeamView.route())
api.add_resource(Lap, "/lap/:team")
api.add_resource(AuthCheck, AuthCheck.route())
api.add_resource(Status, Status.route())

if __name__ == "__main__":
    app.run(debug=True, threaded=True, processes=THREADS)
