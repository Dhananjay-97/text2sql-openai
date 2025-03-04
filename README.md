# text2sql-openai

This project implements a Text-to-SQL application using FastAPI, Streamlit, and OpenAI's API.  It's designed for deployment in a containerized environment (Docker) suitable for Cloudera Machine Learning (CML) workspaces.

## Features:

*   Translates natural language queries into SQL.
*   Uses OpenAI's API for natural language understanding.
*   Leverages FAISS for efficient context retrieval.
*   Supports multiple Oracle databases.
*   Dockerized for easy deployment.
*   Streamlit frontend for user interaction.


## Setup and Deployment:

1.  **Build the Docker image:** `docker build -t your_registry/text2sql-image:latest .`
2.  **Push to registry:** Push the image to your Docker registry.
3.  **Deploy in CML:** Deploy the Docker image in your Cloudera Machine Learning workspace, configuring environment variables, resources, and port mappings.  Refer to the Cloudera documentation for details.
