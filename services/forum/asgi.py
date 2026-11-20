"""ASGI entrypoint: uvicorn services.forum.asgi:app"""
from services.forum.app import create_app

app = create_app()
