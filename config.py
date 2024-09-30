import os


class Config:
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]