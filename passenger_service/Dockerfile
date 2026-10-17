FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install passenger_service deps only (no backend deps).
COPY passenger_service/requirements.txt ./passenger_service/requirements.txt
RUN pip install --no-cache-dir -r ./passenger_service/requirements.txt

# Copy the package as a subdirectory so `python -m passenger_service.main` works
# and all `from passenger_service.x import y` imports resolve.
COPY passenger_service/ ./passenger_service/
COPY pyproject.toml ./

EXPOSE 8002

CMD ["python", "-m", "passenger_service.main"]
