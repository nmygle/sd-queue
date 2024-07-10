from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import gradio as gr

from modules.api import api, models
from modules import script_callbacks
import modules.shared as shared
from secrets import compare_digest

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
    if shared.cmd_opts.api_auth:
        opts_credentials = {}
        for auth in shared.cmd_opts.api_auth.split(","):
            user, password = auth.split(":")
            opts_credentials[user] = password
    
    def auth(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
        if credentials.username in opts_credentials:
            if compare_digest(credentials.password, opts_credentials[credentials.username]):
                return True

        raise HTTPException(status_code=401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Basic"})
    
    @app.post("/sd-queue/txt2img", dependencies=[Depends(auth)])
    async def txt2imgapi(request: Request, txt2imgreq: models.StableDiffusionTxt2ImgProcessingAPI):
        route = next((route for route in request.app.routes if route.path == "/sdapi/v1/txt2img"), None)
        if route:
            task_id, success = task_manager.add_task(route.endpoint, txt2imgreq)
            if success:
                return {"status": "queued", "task_id": task_id}
            else:
                raise HTTPException(status_code=503, detail="Queue is full")
        return {"status": "error"}

    @app.get("/sd-queue/{task_id}/status", dependencies=[Depends(auth)])
    async def get_task_status(task_id: str, request: Request):
        task = task_manager.get_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        response = {"status": task["status"]}

        if "queue_position" in task:
            response["queue_position"] = task["queue_position"]

        if task["status"] == "completed":
            response["result"] = task["result"]
        elif task["status"] == "in-progress":
            route = next((route for route in request.app.routes if route.path == "/sdapi/v1/progress"), None)
            if route:
                progressreq = models.ProgressRequest(skip_current_image=False)
                info = route.endpoint(progressreq)
                response["progress"] = info.progress
                response["eta_relative"] = info.eta_relative
            else:
                print("Route /sdapi/v1/progress not found")
        
        return response
    
    @app.get("/sd-queue/tasks", dependencies=[Depends(auth)])
    async def get_tasks():
        print(opts_credentials)
        return task_manager.get_all_tasks()

    @app.delete("/sd-queue/{task_id}/remove")
    async def remove_specific_task(task_id: str):
        if task_manager.remove_specific_task(task_id):
            return {"status": "success", "message": f"タスク {task_id} が削除されました"}
        else:
            raise HTTPException(status_code=400, detail="タスクが見つからないか、進行中のため削除できません")

    @app.get("/sd-queue/webhooks/{u0}/{u1}", dependencies=[Depends(auth)])
    def send_url(u0, u1):
        from modules import shared
        webhook_url = f'https://discord.com/api/webhooks/{u0}/{u1}'
        message = shared.demo.share_url
        print(message)
        response = send_discord_message(webhook_url, message)


script_callbacks.on_app_started(async_api)
