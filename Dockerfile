FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ACEest_Fitness.py .

ARG APP_VERSION=3.2.4
ENV APP_VERSION=${APP_VERSION}
ENV PORT=5000

EXPOSE 5000
CMD ["python", "ACEest_Fitness.py"]
