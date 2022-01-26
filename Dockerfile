FROM python:3.10
WORKDIR /app
RUN pip install fastapi uvicorn[standard] aioredis hiredis

EXPOSE 8000

COPY ./app /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
