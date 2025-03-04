FROM python:3.10-slim-buster

ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV HR_USER=${HR_USER}
ENV HR_PASSWORD=${HR_PASSWORD}
ENV HR_DSN=${HR_DSN}

ENV BANK_USER=${BANK_USER}
ENV BANK_PASSWORD=${BANK_PASSWORD}
ENV BANK_DSN=${BANK_DSN}

ENV MUSIC_USER=${MUSIC_USER}
ENV MUSIC_PASSWORD=${MUSIC_PASSWORD}
ENV MUSIC_DSN=${MUSIC_DSN}

ENV WATERFALL_USER=${WATERFALL_USER}
ENV WATERFALL_PASSWORD=${WATERFALL_PASSWORD}
ENV WATERFALL_DSN=${WATERFALL_DSN}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/2_app .
COPY entrypoint.sh .
COPY config.yml .
COPY scripts/2_app/images .

EXPOSE 8080
EXPOSE 8501

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

# Example Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8080/ || exit 1

RUN addgroup app && adduser --system --ingroup app app
USER app
