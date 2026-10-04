from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chat import router
from mangum import Mangum


app = FastAPI()
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=['http://localhost:3000'],
    allow_methods=["*"],
    allow_headers=["*"]
)

handler = Mangum(app, lifespan="off")
