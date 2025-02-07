from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from scraper import scrape_jobs
from math import ceil

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

@app.get("/search/")
async def search_remote_jobs(
    query: Optional[str] = Query(None, description="search query (optional for now)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(8, ge=1, le=20, description="Items per page"),  #Sensible limits for safety
) -> Dict[str, Any]:
    """
    Searches for remote jobs, with optional filtering and pagination.
    """

    jobs = scrape_jobs()  # Get all jobs

    # Apply filtering if a query is provided
    if query:
        filtered_jobs = [
            job
            for job in jobs
            if query.lower() in job["position"].lower()
            or query.lower() in job["company"].lower()
            or query.lower() in job["location"].lower()
        ]
    else:
        filtered_jobs = jobs

    # Calculate pagination parameters
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