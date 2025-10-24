FROM python

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY / /lab2/
WORKDIR /lab2

CMD ["python3", "main.py"]