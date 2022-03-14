FROM python:3.7

COPY /app /app
WORKDIR /app

RUN pip3 install -r requirements.txt
COPY /app/static/keys/key /root/key
COPY /app/static/keys/key.pub /root/key.pub

RUN python3 init_db.py

CMD python3 app.py

