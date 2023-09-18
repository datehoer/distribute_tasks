# 任务管理系统

这是一个用Python、FastAPI和SQLite构建的简单任务管理系统，它允许用户创建、执行和监视后台任务。

## 功能特点

- 创建任务并指定脚本路径和参数。
- 后台执行任务，允许并发处理多个任务。
- 监视任务的执行状态和结果。
- 删除不再需要的任务。

## 开始

这些是开始使用任务管理系统的步骤：

### 前提条件

确保你的系统满足以下前提条件：

- Python 3.x

### 安装

在项目根目录下运行以下命令安装依赖项：

```shell
pip install -r requirements.txt
```
运行
使用以下命令启动任务管理系统：
```shell
uvicorn main:app --host 0.0.0.0 --port 8000
```

系统将在 http://localhost:8000/ 上运行。

使用示例
创建任务
使用POST请求创建任务：
```shell
POST /create_task

请求体示例：
{
    "script_path": "scripts/my_script.py",
    "script_args": "arg1|arg2|arg3"
}
```
执行任务
使用POST请求执行任务：
```shell
POST /execute_task/{task_id}
```
检查任务状态
使用GET请求检查任务状态：

```shell
GET /check_status/{task_id}
```
获取任务结果
使用GET请求获取任务结果：

```shell
GET /get_result/{task_id}
```
获取所有任务
使用GET请求获取所有任务：
```shell
GET /get_all_tasks
```
删除任务
使用GET请求删除任务：

```shell
GET /delete_task/{task_id}
```
