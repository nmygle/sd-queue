from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
import gradio as gr

from modules.api import api, models
from modules import script_callbacks
from scripts.task_manager import TaskManager


task_manager = TaskManager()

def async_api(_: gr.Blocks, app: FastAPI):
    @app.post("/kiwi/txt2img")
    async def txt2imgapi(request: Request, txt2imgreq: models.StableDiffusionTxt2ImgProcessingAPI):
        route = next((route for route in request.app.routes if route.path == "/sdapi/v1/txt2img"), None)
        if route:
            task_id = task_manager.add_task(route.endpoint, txt2imgreq)
            return {"status": "queued", "task_id": task_id}
        return {"status": "error"}

    @app.get("/kiwi/{task_id}/status")
    async def get_task_status(task_id: str):
        task = task_manager.get_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["status"] == "completed":
            return {"status": task["status"], "result": task["result"]}
        
        return {"status": task["status"]}
    
    @app.get("/kiwi/tasks")
    async def get_tasks():
        return task_manager.get_all_tasks()

script_callbacks.on_app_started(async_api)
