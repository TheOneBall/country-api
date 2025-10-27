from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Root route for Render health check
@app.get("/")
def home():
    return {"message": "✅ Country Outline API is running successfully!"}

# ✅ Actual API route
@app.get("/api/outline", response_class=PlainTextResponse)
async def get_outline(country: str):
    if not country:
        raise HTTPException(status_code=400, detail="Missing country name")

    url = f"https://en.wikipedia.org/wiki/{country.strip().replace(' ', '_')}"

    try:
        response = httpx.get(url)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch Wikipedia page")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Wikipedia page not found")

    soup = BeautifulSoup(response.text, "html.parser")
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    result = []

    for tag in headings:
        level = int(tag.name[1])
        text = tag.get_text().strip()
        if text:
            result.append(f"{'#' * level} {text}")

    return "\n".join(result)
