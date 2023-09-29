import uuid
from queue import Queue


class TaskManager:
    def __init__(self):
        self.tasks_db = {}
        self.tasks_queue = Queue()

    def add_task(self, func, *args):
        task_id = str(uuid.uuid4())
        self.tasks_db[task_id] = {"status": "in-progress", "result": None}
        self.tasks_queue.put((func, args, task_id))
        return task_id

    def get_status(self, task_id):
        return self.tasks_db.get(task_id)

    def update_status(self, task_id, status, result=None):
        if task_id in self.tasks_db:
            self.tasks_db[task_id]["status"] = status
            if result is not None:
                self.tasks_db[task_id]["result"] = result

    def get_all_tasks(self):
        return self.tasks_db

    def start(self, task_id):
        self.update_status(task_id, "start")

    def complete(self, task_id, result):
        self.update_status(task_id, "completed", result)
