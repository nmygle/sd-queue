import uuid
import threading
from queue import Queue
from collections import OrderedDict


class TaskManager:
    def __init__(self, max_task=30):
        self.max_task = max_task
        self.tasks_db = OrderedDict()
        self.tasks_queue = Queue()
        self.stop_worker = threading.Event()
        self.lock = threading.Lock()
        self._worker_start()

    def _update_status(self, task_id, status, result=None):
        """statusの状態を変更"""
        with self.lock:
            if task_id in self.tasks_db:
                self.tasks_db[task_id]["status"] = status
                if result is not None:
                    self.tasks_db[task_id]["result"] = result

    def _worker(self):
        """workerのループ"""
        while not self.stop_worker.is_set():
            func, args, task_id = self.tasks_queue.get()
            try:
                self._update_status(task_id, "in-progress")
                result = func(*args)
                self._update_status(task_id, "completed", result)
            except Exception as e:
                self._update_status(task_id, "failed", result=str(e))

    def _worker_start(self):
        """workerの開始"""
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.start()

    def worker_stop(self):
        """workerの停止"""
        self.stop_worker.set()
        self.worker_thread.join()

    def add_task(self, func, *args):
        """taskの追加"""
        with self.lock:  # ロックを取得
            while len(self.tasks_db) >= self.max_task:
                self.tasks_db.popitem(last=False)
            task_id = str(uuid.uuid4())
            self.tasks_db[task_id] = {"status": "pending", "result": None}
        
        self.tasks_queue.put((func, args, task_id))
        return task_id

    def get_status(self, task_id):
        """状態の取得"""
        with self.lock:
            return self.tasks_db.get(task_id)

    def get_all_tasks(self):
        """全状態の取得"""
        with self.lock:
            return {k: v["status"] for k, v in self.tasks_db.items()}

    def remove_specific_task(self, task_id):
        """pending taskの削除"""
        with self.lock:
            if task_id in self.tasks_db and self.tasks_db[task_id]["status"] == "pending":
                # tasks_dbから削除
                del self.tasks_db[task_id]
                
                # tasks_queueから削除
                # 注意: これは非効率的な方法です。大規模なシステムでは別の方法を検討する必要があります。
                temp_queue = Queue()
                while not self.tasks_queue.empty():
                    item = self.tasks_queue.get()
                    if item[2] != task_id:  # item[2]はtask_id
                        temp_queue.put(item)
                self.tasks_queue = temp_queue
                
                return True
        return False
