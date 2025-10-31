from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "email": "23f2004078@ds.study.iitm.ac.in",
    }
    return {
        "message": "Hello from Codespaces!"
    }
