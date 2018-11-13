FROM python:3.6

COPY ./Utils ./Utils
COPY ./Tests ./Tests
COPY ./Scrapper ./Scrapper

COPY app.py .

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY run_tests.sh .

RUN chmod -R 777 run_tests.sh

RUN ./run_tests.sh

EXPOSE 5000

CMD ["python", "app.py"]
