import threading

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
import gradio as gr

from modules.api import api, models
from modules import script_callbacks
from scripts.task_manager import TaskManager


task_manager = TaskManager()

def worker():
    while True:
        func, args, task_id = task_manager.tasks_queue.get()
        try:
            task_manager.start(task_id)
            result = func(*args)
            task_manager.complete(task_id, result)
        except Exception as e:
            task_manager.update_status(task_id, "error", str(e))

worker_thread = threading.Thread(target=worker)
worker_thread.start()

def async_api(_: gr.Blocks, app: FastAPI):
    @app.post("/kiwi/txt2img")
    async def txt2imgapi(request: Request, txt2imgreq: models.StableDiffusionTxt2ImgProcessingAPI):
        route = next((route for route in request.app.routes if route.path == "/sdapi/v1/txt2img"), None)
        if route:
            task_id = task_manager.add_task(route.endpoint, txt2imgreq)
            return {"status": "Task is running in the background!", "task_id": task_id}
        return {"status": "error", "task_id": task_id}

    @app.get("/kiwi/{task_id}/status")
    async def get_task_status(task_id: str):
        task = task_manager.get_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["status"] == "completed":
            return {"status": task["status"], "result": task["result"]}
        return {"status": task["status"]}
    
    @app.get("/kiwi/get_tasks")
    async def get_tasks():
        return task_manager.get_all_tasks()


script_callbacks.on_app_started(async_api)

