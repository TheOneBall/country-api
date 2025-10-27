from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import httpx
from bs4 import BeautifulSoup

app = FastAPI(
    title="GlobalEdu Country Information API",
    description="API to fetch and generate Markdown outlines from Wikipedia country pages",
    version="1.0.0"
)

# Enable CORS for all origins (Requirement 5)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET"],  # Only allow GET requests
    allow_headers=["*"],
)


def fetch_wikipedia_page(country: str) -> str:
    """
    Fetch the HTML content of a Wikipedia page for the given country.
    (Requirement 2: Fetching Wikipedia Content)
    
    Args:
        country: Name of the country
        
    Returns:
        HTML content of the Wikipedia page
        
    Raises:
        HTTPException: If the page cannot be fetched
    """
    # Format country name for Wikipedia URL (replace spaces with underscores)
    country_formatted = country.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{country_formatted}"
    
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Wikipedia page not found for country: {country}"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Wikipedia page: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Wikipedia page: {str(e)}"
        )


def extract_headings(html_content: str) -> list[tuple[int, str]]:
    """
    Extract all headings (H1 to H6) from HTML content, maintaining order.
    (Requirement 3: Extracting Headings)
    
    Args:
        html_content: HTML string to parse
        
    Returns:
        List of tuples (heading_level, heading_text)
        heading_level is 1-6 for H1-H6
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main content area (Wikipedia uses specific divs)
    content = soup.find('div', {'id': 'mw-content-text'})
    if not content:
        content = soup
    
    headings = []
    
    # Extract all heading tags H1-H6 in order, maintaining sequence
    for heading in content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        # Get the heading level (1-6)
        level = int(heading.name[1])
        
        # Get the text content, removing edit links and references
        text = heading.get_text(strip=True)
        
        # Remove [edit] and similar markers that Wikipedia includes
        text = text.replace('[edit]', '').strip()
        
        # Skip empty headings
        if text:
            headings.append((level, text))
    
    return headings


def generate_markdown_outline(headings: list[tuple[int, str]]) -> str:
    """
    Generate a Markdown-formatted outline from headings.
    (Requirement 4: Generating Markdown Outline with # symbols)
    
    Args:
        headings: List of tuples (heading_level, heading_text)
        
    Returns:
        Markdown-formatted outline string with headings beginning with #
    """
    if not headings:
        return "No headings found."
    
    markdown_lines = ["# Contents\n"]
    
    for level, text in headings:
        # Convert heading level to number of # symbols
        # H1 = #, H2 = ##, H3 = ###, etc.
        hash_marks = "#" * level
        
        # Create the markdown line with # prefix
        markdown_lines.append(f"{hash_marks} {text}")
    
    return "\n".join(markdown_lines)


@app.get("/")
async def root():
    """
    Root endpoint with API information and usage instructions.
    """
    return {
        "message": "GlobalEdu Country Information API",
        "description": "Fetch structured Wikipedia country outlines in Markdown format",
        "usage": "GET /api/outline?country=<country_name>",
        "examples": [
            "/api/outline?country=Vanuatu",
            "/api/outline?country=France",
            "/api/outline?country=New%20Zealand"
        ],
        "documentation": "/docs"
    }


@app.get("/api/outline", response_class=PlainTextResponse)
async def get_country_outline(
    country: str = Query(
        ..., 
        description="Name of the country to fetch outline for",
        example="Vanuatu"
    )
):
    """
    Fetch Wikipedia page for a country and return a Markdown outline of its headings.
    (Requirement 1: API endpoint with country query parameter)
    
    This endpoint:
    - Accepts a country name as query parameter
    - Fetches the Wikipedia page for that country
    - Extracts all headings (H1-H6) in order
    - Returns a Markdown-formatted outline with # symbols
    - Supports CORS for cross-origin requests
    
    Args:
        country: Name of the country (query parameter)
        
    Returns:
        Plain text Markdown outline with headings prefixed by #
        
    Example:
        GET /api/outline?country=Vanuatu
        
    Response:
        # Contents
        
        # Vanuatu
        ## Etymology
        ## History
        ### Prehistory
        ...
    """
    # Validate input
    if not country or not country.strip():
        raise HTTPException(
            status_code=400,
            detail="Country parameter cannot be empty"
        )
    
    # Step 1: Fetch the Wikipedia page
    html_content = fetch_wikipedia_page(country)
    
    # Step 2: Extract headings (H1-H6) in order
    headings = extract_headings(html_content)
    
    if not headings:
        raise HTTPException(
            status_code=404,
            detail=f"No headings found for country: {country}"
        )
    
    # Step 3: Generate Markdown outline with # symbols
    markdown_outline = generate_markdown_outline(headings)
    
    return markdown_outline


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {
        "status": "healthy",
        "message": "GlobalEdu Country Information API is operational"
    }


# To run this application:
# 1. Install dependencies: pip install fastapi uvicorn httpx beautifulsoup4
# 2. Run server: uvicorn main:app --reload
# 3. Access API: http://localhost:8000/api/outline?country=Vanuatu
# 4. View docs: http://localhost:8000/docs