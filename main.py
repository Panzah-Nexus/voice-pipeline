# main.py  – thin wrapper so the Cerebrium CLI is happy
from src.main import app   # re-export the real FastAPI instance

# Optional: let you run `python main.py` locally if you like
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)
