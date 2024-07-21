import uuid
import threading
from collections import OrderedDict, deque

class TaskManager:
    def __init__(self, max_task=30):
        self.max_task = max_task
        self.tasks_db = OrderedDict()
        self.tasks_queue = deque()
        self.stop_worker = threading.Event()
        self.lock = threading.Lock()
        self._worker_start()

    def _update_status(self, task_id, status, result=None):
        with self.lock:
            if task_id in self.tasks_db:
                self.tasks_db[task_id]["status"] = status
                if result is not None:
                    self.tasks_db[task_id]["result"] = result

    def _worker(self):
        while not self.stop_worker.is_set():
            if self.tasks_queue:
                with self.lock:
                    func, args, task_id = self.tasks_queue.popleft()
                try:
                    self._update_status(task_id, "in-progress")
                    result = func(*args)
                    self._update_status(task_id, "completed", result)
                except Exception as e:
                    self._update_status(task_id, "failed", result=str(e))
            else:
                self.stop_worker.wait(timeout=0.1)

    def _worker_start(self):
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.start()

    def worker_stop(self):
        self.stop_worker.set()
        self.worker_thread.join()

    def add_task(self, func, *args):
        with self.lock:
            if len(self.tasks_db) >= self.max_task:
                # 最も古いタスクを探す
                oldest_task_id = next(iter(self.tasks_db))
                oldest_task = self.tasks_db[oldest_task_id]
                
                if oldest_task['status'] in ['in-progress', 'pending']:
                    return None, False
                
                self.tasks_db.popitem(last=False)
                self.tasks_queue = deque((f, a, tid) for f, a, tid in self.tasks_queue if tid != oldest_task_id)
    
            task_id = str(uuid.uuid4())
            self.tasks_db[task_id] = {"status": "pending", "result": None}
            self.tasks_queue.append((func, args, task_id))
            
        return task_id, True

    def get_status(self, task_id):
        with self.lock:
            task = self.tasks_db.get(task_id)
            if task:
                if task['status'] == 'pending':
                    pending_tasks = [tid for _, _, tid in self.tasks_queue if self.tasks_db[tid]['status'] == 'pending']
                    queue_position = pending_tasks.index(task_id) + 1 
                    task['queue_position'] = queue_position
                else:
                    task['queue_position'] = None
        return task

    def get_all_tasks(self):
        with self.lock:
            return {k: v["status"] for k, v in self.tasks_db.items()}

    def remove_specific_task(self, task_id):
        with self.lock:
            if task_id in self.tasks_db and self.tasks_db[task_id]["status"] == "pending":
                del self.tasks_db[task_id]
                self.tasks_queue = deque(item for item in self.tasks_queue if item[2] != task_id)
                return True
        return False
