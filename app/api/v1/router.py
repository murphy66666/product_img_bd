from fastapi import APIRouter

from app.api.v1 import auth, gallery, generation, health, sessions, templates, uploads

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(sessions.router)
api_router.include_router(gallery.router)
api_router.include_router(generation.router)
api_router.include_router(templates.router)
api_router.include_router(uploads.router)
