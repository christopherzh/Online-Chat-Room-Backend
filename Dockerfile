FROM python:3.10
WORKDIR /app
RUN pip install fastapi uvicorn[standard] aioredis hiredis grpcio==1.43.0 grpcio-tools==1.43.0 grpcio-reflection==1.43.0 python-multipart

EXPOSE 8000 8001 50051

COPY ./app /app

CMD ["sh","./start.sh"]
