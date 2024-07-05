from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
import gradio as gr

from modules.api import api, models
from modules import script_callbacks
from scripts.task_manager import TaskManager

import requests

def send_discord_message(webhook_url, content):
    data = {
        "content": content
    }
    response = requests.post(webhook_url, json=data)
    return response

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
    async def get_task_status(task_id: str, request: Request):
        task = task_manager.get_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["status"] == "completed":
            return {"status": task["status"], "result": task["result"]}
        elif task["status"] == "in-progress":
            route = next((route for route in request.app.routes if route.path == "/sdapi/v1/progress"), None)
            if route:
                progressreq = models.ProgressRequest(skip_current_image=False)
                info = route.endpoint(progressreq)
                # print(info.progress, info.eta_relative)
                return {"status": task["status"], "progress": info.progress, "eta_relative": info.eta_relative}
            else:
                print("Route /sdapi/v1/progress not found")
        
        return {"status": task["status"]}
    
    @app.get("/kiwi/tasks")
    async def get_tasks():
        return task_manager.get_all_tasks()

    @app.get("/kiwi/webhooks/{u0}/{u1}")
    def send_url(u0, u1):
        from modules import shared
        webhook_url = f'https://discord.com/api/webhooks/{u0}/{u1}'
        message = shared.demo.share_url
        print(message)
        response = send_discord_message(webhook_url, message)


script_callbacks.on_app_started(async_api)
