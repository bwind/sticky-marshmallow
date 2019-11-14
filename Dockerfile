FROM python:3.8

RUN echo "alias l='ls -lahF --color=auto'" >> /root/.bashrc

RUN echo "python -m pytest --disable-warnings -x" >> /root/.bash_history

WORKDIR /app

COPY requirements*.txt /app/

RUN pip install -r requirements-test.txt

COPY . /app
