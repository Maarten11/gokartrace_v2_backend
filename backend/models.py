from datetime import datetime
import os
import bcrypt
from sqlalchemy import TEXT, VARCHAR, Column, Interval, TIMESTAMP, Integer, create_engine, Table, insert, select, LargeBinary, true
from sqlalchemy.sql import text
from sqlalchemy.orm import declarative_base, sessionmaker
from os import environ

Base = declarative_base()

# Determine amount of threads
THREADS = 30


# Extract info from env
postgres_user = environ["POSTGRES_USER"]
postgres_password = environ["POSTGRES_PASSWORD"]
postgres_db = environ["POSTGRES"]
postgres_port = environ["POSTGRES_PORT"]

connect_str = f"postgresql://{postgres_user}:{postgres_password}@db:{postgres_port}/{postgres_db}"
print(connect_str, flush=True)
engine = create_engine(connect_str, pool_size=THREADS)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(VARCHAR(50), nullable=False)
    # salt = Column(VARCHAR(50), nullable=False)
    password = Column(LargeBinary(), nullable=False)

    def __repr__(self) -> str:
        return f"User ({self.id}): {self.username}"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    teamname = Column(VARCHAR(50), nullable=False)
    laps = Column(Integer)
    lastlap: datetime = Column(TIMESTAMP(False))
    laptime = Column(Interval(second_precision=1))

    def to_dict(self) -> dict:
        """Transform competitor data to serializable data

        :return: dictionary
        """
        self.laptime = max(self.laptime, 1) # Ensure laptime isn't 0
        elapsed = int((datetime.now() - self.lastlap).total_seconds())
        progress = min(elapsed*100 // self.laptime, 100)
        remaining = max(0, self.laptime - elapsed)
        result = {"name": self.teamname, "laps": self.laps, "lastlap": self.lastlap.isoformat(), "laptime": self.laptime, "elapsed": elapsed, "progress": progress, "remaining": remaining}
        return result

    def __repr__(self) -> str:
        return f"Team ({self.id}): {self.teamname}. # Laps: {self.laps} Last lap: {self.lastlap} in {self.laptime} seconds"

sessions = sessionmaker(engine)

Base.metadata.create_all(engine)
team_table: Table = Team.__table__
user_table: Table = User.__table__


def new_lap(team_name: str):
    with sessions() as session:
        t = text("UPDATE teams SET laptime = GREATEST(1, EXTRACT(epoch FROM (now() - lastlap))), \
                 lastlap = now(), laps = laps + 1 WHERE teamname=:team;").bindparams(team=team_name)
        session.execute(t)
        session.commit()
    # team_table.update().where(teamname = team_name).values(laptime=(func.now() - team_table.c.lastlap), lastlap=func.now())

def init_default_user():
    with sessions() as session:
        username = os.environ.get("DEFAULT_USER", "default_user_name")
        # username = "default_user_name" # TODO change to better username stored in .env file

        # Check if default user already exists
        result = session.execute(select(User).where(User.username == username)).scalar_one_or_none()

        print(result, flush=True)

        if result:
            print("Denied", flush=True)
            return

        # Initialise default user
        plain_password = os.environ.get("DEFAULT_PASS", "default_user_password")
        # plain_password = "default_user_password" # TODO change to better password stored in .env file
        password = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt())
        query = text("INSERT INTO users VALUES(DEFAULT, :username, :password);")\
        .bindparams(username = username, password = password)

        print(query, flush=True)

        session.execute(query)

        session.commit()

        print("Default user created", flush=True)


