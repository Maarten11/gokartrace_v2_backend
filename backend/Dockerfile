FROM python:3.9.1

RUN mkdir /usr/src/back-end
WORKDIR /usr/src/back-end
# ENV FLASK_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
# ENV FLASK_RUN_HOST=127.0.0.1

COPY ./requirements.txt ./

RUN pip install -r ./requirements.txt

COPY . .

EXPOSE 5000

CMD ["flask", "run"]
