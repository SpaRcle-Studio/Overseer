from fastapi import FastAPI
from typing import Optional
from src.message import *
from multiprocessing import Queue

class APIManager(FastAPI):
    def __init__(self, task_queue: Queue, result_queue: Queue):
        super().__init__()

        self.task_queue = task_queue
        self.result_queue = result_queue

        self.add_api_route("/", self.read_root, methods=["GET"])
        self.add_api_route("/status", self.status, methods=["GET"])
        self.add_api_route("/items/{item_id}", self.read_item, methods=["GET"])

    def __del__(self):
        print("APIManager : exiting.")

    def status(self):
        return {"status": 6969}

    def read_root(self):
        return {"message": "Hello, little naughty boy!"}

    def read_item(self, item_id: int, q: Optional[str] = None):
        return {"item_id": item_id, "q": q}
