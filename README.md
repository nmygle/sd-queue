### **Description**

sd-queue is available as an extension for Stable Diffusion webui.It is an extension that provides an API primarily for queuing tasks, using a simple task manager created with Pure Python's deque and threading.

- /sd-queue/login
    - Returns status and version.
- /sd-queue/txt2img
    - Adds txt2img to the queue.
    - At this time, it returns the status and task_id.
- /sd-queue/{task_id}/status
    - Returns the status by passing the task_id.
- /sd-queue/{task_id}/remove
    - Removes tasks that are in pending status.

### Features

- Supports authentication.
    - Please add the following options to set the username and password.

```bash
--api-auth user:passwd
```

- The maximum number of tasks is set at 30.
    - If tasks are added in excess of 30, the complete task will be deleted.
    - If necessary, adjust max_task in TaskManager.

### Caution

- This is designed for personal use.
- It is recommended that intermediary servers and Redis be utilized for larger scale service operations.
