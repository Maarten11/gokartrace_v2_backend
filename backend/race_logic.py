import json
from sqlalchemy import asc, insert, select, text
from auth import auth_valid
from flask import make_response, request
from flask_restful import Resource
from models import sessions, Team

class Status(Resource):
    def route():
        return "/status"

    def get(self):
        with sessions() as session:
            query = text("SELECT status FROM races WHERE name = 'default';")
            result = session.execute(query).scalar_one_or_none()
            session.commit()

            if result is None:
                return make_response("Database initialised wrong", 500)

            return make_response(result, 200)

    @auth_valid
    def post(self):

        # print(request.data, request.form, flush=True)

        new_status = request.data.decode()

        with sessions() as session:
            query = text("UPDATE races SET status = :status WHERE name='default';").bindparams(status=new_status)
            result = session.execute(query)
            if new_status == "Started":
                query = text("UPDATE teams SET lastlap = now();")
                result = session.execute(query)
            session.commit()

            print(result, flush=True)

            return make_response("Status Updated", 200)


# class StartRace(Resource):
#     def route():
#         return "/start"

#     @auth_valid
#     def post(self):
#         with sessions() as session:
#             query = text("UPDATE races SET status = 'Started' WHERE name = 'default'")
#             result = session.execute(query)
#             session.commit()

#         return make_response("Updated", 200)

# class PauseRace(Resource):
#     def route():
#         return "/pause"

#     @auth_valid
#     def post(self):
#         with sessions() as session:
#             query = text("UPDATE races SET status = 'Paused' WHERE name = 'default'")
#             result = session.execute(query)
#             session.commit()

#         return make_response("Updated", 200)

# class StopRace(Resource):
#     def route():
#         return "/stop"

#     @auth_valid
#     def post(self):
#         with sessions() as session:
#             query = text("UPDATE races SET status = 'Stopped' WHERE name = 'default'")
#             result = session.execute(query)
#             session.commit()

#         return make_response("Updated", 200)

class CountRound(Resource):
    def route():
        return "/count"

    @auth_valid
    def post(self):

        # Extract body
        body = request.form

        # Check if team specified
        if "team" not in body.keys():
            return make_response("Parameter 'team' was not specified. Team name required for this operation", 400)
        if "lapcount" not in body.keys():
            return make_response("Parameter 'lapcount' was not specified. Lap count required for this operation.", 400)

        # Extract team name
        team_name = body["team"]
        lap_count = body["lapcount"]

        # Update team laps
        with sessions() as session:
            # Can only count when a race is running
            t = text("SELECT status FROM races WHERE status = 'Started'")
            result = session.execute(t).scalar_one_or_none()

            if result is None:
                return make_response("Cannot edit teams when race is ongoing", 409)

            t = text("UPDATE teams SET laptime = EXTRACT(epoch FROM (now() - lastlap)), \
            lastlap = now(), laps = :lapcount WHERE teamname=:team").bindparams(lapcount=lap_count, team=team_name)
            result = session.execute(t)
            # session.commit()
            print(result, flush=True)

            session.commit()

        return make_response("Succesfully updated", 200)

class Teams(Resource):
    def route():
        return "/teams"

    def get(self):
        with sessions() as session:
            teams: list[Team] = session.execute(select(Team).order_by(asc(Team.teamname))).scalars().all()

            if teams is None:
                return make_response("There is no ongoing race", 404)

            # Result is a list of teams
            return json.dumps([t.to_dict() for t in teams])

    def post(self):

        form = request.form

        if not "teams" in form.keys():
            return make_response("Missing attribute form", 400)

        teams = json.loads(form["teams"])

        print(teams, flush=True)

        with sessions() as session:
            # Can only post teams when the race is stopped
            t = text("SELECT status FROM races WHERE status != 'Stopped'")
            result = session.execute(t).scalar_one_or_none()

            if result is not None:
                return make_response("Cannot edit teams when race is ongoing", 409)

            t = text("TRUNCATE teams;")
            result = session.execute(t)

            result = session.execute(insert(Team).values(teams))

            session.commit()


class TeamView(Resource):
    def route():
        return "/teams/<team>"

    def get(self, team):
        with sessions() as session:
            result = session.execute(select(Team).where(Team.teamname == team)).scalar_one_or_none()

            # No matching team found
            if result is None:
                return make_response(f"Team with teamname '{team}' does not exist", 404)

            return json.dumps(result.to_dict())

    @auth_valid
    def post(self, team):
        with sessions() as session:
            # Todo: can't add team if race is already ongoing
            # Check if race is already ongoing
            result = session.execute(select(Team).where(Team.laps > 0)).scalar_one_or_none()
            if result is not None:
                return make_response("Cannot add teams to race that has already started", 409)

            # Insert team
            session.execute(insert(Team).values(teamname=team))
            session.commit()
            return make_response("Team succesfully added", 200)
