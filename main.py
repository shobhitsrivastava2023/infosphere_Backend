from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from scraper import scrape_jobs
from math import ceil
import asyncio
import json

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8000/",
    "*",  # to be removed in production
]

origins = [
    "http://localhost:3000",  # For local development
    "https://your-netlify-site.netlify.app",  # Your Netlify production URL
    "https://www.your-custom-domain.com", #If you have a custom domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory data storage
job_data: List[Dict] = []

async def populate_job_data():
    """
    Scrapes job data and stores it in the in-memory `job_data` list.
    """
    global job_data  # Access the global variable
    jobs = scrape_jobs()
    if jobs:
        # Safely persist the data to a file (e.g., JSON) for persistence
        try:
            with open("job_data.json", "w") as f:
                json.dump(jobs, f)  # Save the new jobs directly
            print(f"Successfully saved {len(jobs)} jobs to job_data.json.")
        except Exception as e:
            print(f"Error saving job_data to JSON: {e}")

        job_data = jobs  # Update the in-memory data AFTER successful save
        print(f"Successfully populated in-memory job_data with {len(jobs)} jobs.")
    else:
        print("Failed to scrape jobs.")

@app.on_event("startup")
async def startup_event():
    """
    Runs on server startup to initialize in-memory data and start background task.
    """
    global job_data  
    try:
        with open("job_data.json", "r") as f:
            job_data = json.load(f)
            print("Loaded job_data from job_data.json")
    except FileNotFoundError:
        print("job_data.json not found. Starting with empty data.")
    except Exception as e:
        print(f"Error loading job_data from JSON: {e}")

    asyncio.create_task(scheduled_scraping()) # Start the scheduled scraping

async def scheduled_scraping():
    """
    A background task that scrapes and updates the in-memory data periodically.
    """
    while True:
        print("Running scheduled scraping...")
        await populate_job_data()
        await asyncio.sleep(3600)  # Scrape every hour (adjust as needed)

@app.get("/search/")
async def search_remote_jobs(
    query: Optional[str] = Query(None, description="search query (optional for now)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(8, ge=1, le=20, description="Items per page"),  #Sensible limits for safety
) -> Dict[str, Any]:
    """
    Searches for remote jobs, with optional filtering and pagination.
    """

    global job_data  # Access the global variable

    # Apply filtering if a query is provided
    if query:
        filtered_jobs = [
            job
            for job in job_data
            if query.lower() in job["position"].lower()
            or query.lower() in job["company"].lower()
            or query.lower() in job["location"].lower()
        ]
    else:
        filtered_jobs = job_data

    # Pagination logic
    total_jobs = len(filtered_jobs)
    total_pages = ceil(total_jobs / limit)
    start_index = (page - 1) * limit
    end_index = start_index + limit

    # Paginate the results
    paginated_jobs = filtered_jobs[start_index:end_index]

    return {
        "jobs": paginated_jobs,
        "total_pages": total_pages,
        "current_page": page,  # Optional, but helpful for the frontend
        "total_jobs": total_jobs, #Optional, helpful for the frontend
    }