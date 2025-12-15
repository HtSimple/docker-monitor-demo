FROM python:3.9-slim

WORKDIR /app
RUN pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY train.py /app/

ENTRYPOINT ["python", "train.py"]