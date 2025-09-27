from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import upload, process, template

app = FastAPI(title="eBay Blu-ray Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(process.router)
app.include_router(template.router)

@app.get("/")
async def root():
    return {"message": "eBay Blu-ray Assistant API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)