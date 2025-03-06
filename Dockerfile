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

FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x entrypoint.sh
EXPOSE 8080 8501
ENTRYPOINT ["./entrypoint.sh"]
 
Run the below command to build the docker image: (Make sure you are into the path where the Dockerfile is available)
docker build -t text2sql . 
 
Check if you go the image build by using command: 
docker images
 
If you want to run the container of this image and check then use the below command: 
docker run -p 8080:8080 -p 8051:8051 --name text2sql-container text2sql

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY scripts/2_app .
# COPY entrypoint.sh .
# COPY config.yml .
# COPY scripts/2_app/images .

# EXPOSE 8080
# EXPOSE 8501

# ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

# # Example Healthcheck
# HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8080/ || exit 1

# RUN addgroup app && adduser --system --ingroup app app
# USER app
