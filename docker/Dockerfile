FROM apache/spark:3.5.3-python3

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/spark/python:/opt/spark/python/lib/pyspark.zip:/opt/spark/python/lib/py4j-0.10.9.7-src.zip
USER root

# The upstream Spark image exposes Python 3.8 as `python3` only.  Add the
# conventional alias and use a Python-3.8 compatible dependency set for the
# cluster image; the portable host image keeps the newer root requirements.
RUN ln -sf /usr/bin/python3 /usr/local/bin/python \
    && python3 -m pip install --no-cache-dir --upgrade 'pip<25'
COPY docker/requirements-cluster.txt ./requirements-cluster.txt
# The development network intermittently resets pypi.org TLS connections;
# this public mirror makes the reproducible image build complete reliably.
RUN python3 -m pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-cluster.txt
COPY backend ./backend
COPY pipeline ./pipeline
COPY database ./database
COPY frontend ./frontend
COPY data ./data

EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
