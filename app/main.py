from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import config, import_recipe, ocr, structure

app = FastAPI()

app.include_router(config.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(structure.router, prefix="/api")
app.include_router(import_recipe.router, prefix="/api")

app.mount("/imgs", StaticFiles(directory="app/imgs"), name="imgs")
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
