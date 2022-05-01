FROM python:3.10
WORKDIR /app
RUN pip install fastapi uvicorn[standard] aioredis hiredis grpcio==1.43.0 grpcio-tools==1.43.0 grpcio-reflection==1.43.0 python-multipart

EXPOSE 8000

COPY ./app /app

CMD ["uvicorn", "im_system:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "ws_system:app", "--host", "0.0.0.0", "--port", "8001"]
