from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
import time

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# ✅ Root route - returns plain text (not JSON)
@app.get("/", response_class=PlainTextResponse)
def home():
    return "GlobalEdu Country Outline API - Ready"

# ✅ Health check endpoint
@app.head("/")
def health_check():
    return {"status": "ok"}

# ✅ API endpoint
@app.get("/api/outline", response_class=PlainTextResponse)
async def get_outline(country: str = None):
    """
    Get markdown outline of Wikipedia page for a country
    Query parameter: ?country=CountryName
    """
    if not country or country.strip() == "":
        return "# Error\n\nCountry parameter is required.\n\nUsage: /api/outline?country=CountryName"
    
    try:
        country_clean = country.strip().replace(' ', '_')
        url = f"https://en.wikipedia.org/wiki/{country_clean}"
        
        # Add headers to avoid Wikipedia blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Polite delay
        time.sleep(0.5)
        
        # Fetch Wikipedia page
        response = httpx.get(url, headers=headers, timeout=15)
        
        if response.status_code == 404:
            return f"# Error\n\nWikipedia page not found for '{country}'"
        
        if response.status_code != 200:
            return f"# Error\n\nHTTP Error {response.status_code}"
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find main content area
        content = soup.find('div', {'id': 'mw-content-text'})
        if not content:
            content = soup
        
        # Extract headings
        headings = content.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        
        if not headings:
            return f"# {country}\n\nNo headings found on Wikipedia page."
        
        result = []
        
        for tag in headings:
            level = int(tag.name[1])
            text = tag.get_text(strip=True)
            
            # Clean up
            text = text.replace('[edit]', '').strip()
            
            # Skip empty or navigation headings
            if not text or text.lower() in ['contents', 'navigation', 'references', 'see also']:
                continue
            
            # Create markdown
            result.append(f"{'#' * level} {text}")
        
        if not result:
            return f"# {country}\n\nNo valid headings found."
        
        return "\n\n".join(result)
    
    except httpx.TimeoutException:
        return "# Error\n\nRequest timed out"
    
    except Exception as e:
        return f"# Error\n\n{str(e)}"
