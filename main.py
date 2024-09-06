from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/query/")
async def query_rooms():
    return {"message": f"Hello World from query"}
