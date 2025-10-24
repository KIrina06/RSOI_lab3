FROM python:latest
COPY . /src
WORKDIR /src
RUN pip install --no-cache-dir -r requirements.txt
COPY . /src
CMD ["python3", "main.py"]
