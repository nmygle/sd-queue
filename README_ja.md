### **説明**

sd-queueはStable Diffusion webuiの拡張機能として利用できます。

dequeとthreadingのPure Pythonで作成した簡易的なtask managerを利用して、主にタスクをキューイングするためのAPIを用意する拡張です。

- /sd-queue/login
    - statusとversionを返します。
- /sd-queue/txt2img
    - txt2imgをキューに追加します。
    - この時、statusとtask_idを返します。
- /sd-queue/{task_id}/status
    - task_idを渡すことでstatusを返します。
- /sd-queue/{task_id}/remove
    - pendingになっているタスクをremoveします。

### 特徴

- 認証に対応しています。
    - 以下のオプションを追加して、ユーザー名とパスワードを設定してください。
    
    ```bash
    --api-auth user:passwd
    ```
    
- タスクの最大数は30としています。
    - 30を超えてタスクが追加されるとcompleteのタスクが削除されます。
    - 必要があればTaskManagerのmax_taskを調整してください。

### 注意

- これは個人的な利用を想定した作りとなっています。
- より大規模なサービスの運用には仲介サーバやRedisなどを活用することをお勧めします。
