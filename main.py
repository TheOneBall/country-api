from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class AttachmentRequest(BaseModel):
    attachments: dict

@app.post("/file")
def detect_mime(request: AttachmentRequest):
    url = request.attachments.get("url", "")
    
    # Extract MIME type from data URI (format: data:MIME_TYPE;base64,...)
    if url.startswith("data:"):
        mime_part = url.split(";")[0].replace("data:", "")
        main_type = mime_part.split("/")[0]
        
        if main_type in ["image", "text", "application"]:
            return {"type": main_type}
    
    return {"type": "unknown"}