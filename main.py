from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import users_router
from pydantic import BaseModel
import uvicorn

class HealthResponse(BaseModel):
    status: str

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
prefix = "/api/v1"
app.include_router(router=users_router, prefix=f"{prefix}", tags=["auth"])

@app.get("/", response_model=HealthResponse)
async def health():
    return HealthResponse(status="Ok")

if __name__ == "__main__":
    uvicorn.run("main:app", port=1515, log_level="info")