#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CardioMind AI Diagnosis Service API

Provides a RESTful API endpoint to run medical diagnosis based on case data.
This server is designed to be run inside a Docker container.

Endpoint:
  POST /cardiomind
    - Receives patient medical record in JSON format.
    - Executes the diagnosis workflow.
    - Returns the final diagnosis report.

Usage (inside Docker):
  uvicorn api_server:app --host 0.0.0.0 --port 8080
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# 使用包导入，不再修改 sys.path
from app.agents.medical_agent_orchestrator import MedicalAgentOrchestrator
from app.utils.case_converter import convert_to_system_format

# --- FastAPI App Initialization ---
app = FastAPI(
    title="CardioMind AI Diagnosis Service",
    description="An API for running AI-powered medical diagnosis.",
    version="1.0.0"
)

# --- Global Objects ---
# Instantiate the orchestrator once at startup.
# This is crucial for performance as it pre-loads necessary models and resources.
print("Initializing MedicalAgentOrchestrator...")
try:
    orchestrator = MedicalAgentOrchestrator()
    print("Orchestrator initialized successfully.")
except Exception as e:
    print(f"FATAL: Failed to initialize MedicalAgentOrchestrator: {e}")
    # In a real-world scenario, you might want to exit if the core component fails to load.
    orchestrator = None

# --- API Endpoints ---
@app.post("/cardiomind")
async def run_cardiomind_diagnosis(request: Request):
    """
    Receives a medical case in JSON format, runs the diagnosis workflow,
    and returns the resulting report.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=503, 
            detail="Service Unavailable: The diagnosis engine is not initialized."
        )

    try:
        # 1. Get raw JSON data from the request body
        case_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format in request body.")

    try:
        # 2. Convert the input data to the system's internal format
        # Reusing the stable logic from test cases ensures consistency.
        patient_data = convert_to_system_format(case_data)

        # 3. Create a diagnosis session and execute the workflow
        session_id = orchestrator.create_diagnosis_session(patient_data)
        report = orchestrator.execute_diagnosis_workflow(patient_data, session_id)

        # 4. Return the report as a JSON response
        return JSONResponse(content=report, status_code=200)

    except FileNotFoundError as e:
        # This might be triggered if the orchestrator logic expects a file that doesn't exist
        raise HTTPException(status_code=500, detail=f"Internal Server Error: A required file was not found: {e}")
    except Exception as e:
        # Catch-all for other unexpected errors during the diagnosis process
        print(f"ERROR: An unexpected error occurred during diagnosis: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/health", summary="Health Check")
async def health_check():
    """
    Simple health check endpoint to verify that the service is running.
    """
    return {"status": "ok"}

# --- Main execution block for local testing ---
if __name__ == "__main__":
    print("Starting CardioMind API server for local testing...")
    # This block is for running the server directly on your local machine without Docker.
    # It's useful for quick debugging.
    # The Docker container will use the 'uvicorn api_server:app ...' command directly.
    uvicorn.run(app, host="127.0.0.1", port=8080)