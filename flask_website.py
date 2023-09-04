import uvicorn
import subprocess
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from ast import literal_eval
import threading
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
engine = create_engine('sqlite:///tasks.db', connect_args={"check_same_thread": False}, echo=True)
task_lock = threading.Lock()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源。在生产环境中，你应该设置特定的来源。
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

class CreateTaskData(BaseModel):
    script_path: str
    script_args: str


with engine.connect() as connection:
    connection.execute(text('''CREATE TABLE IF NOT EXISTS tasks
                               (id INTEGER PRIMARY KEY,
                               script_path TEXT,
                               script_args TEXT,
                               status TEXT,
                               result TEXT)'''))


def execute_task_in_subprocess(task_id, script_path, script_args):
    with engine.connect() as connection:
        connection.execute(text("UPDATE tasks SET status=:status WHERE id=:id"), {"status": "进行中", "id": task_id})

        process = subprocess.run(
            ["python", script_path, *script_args.split()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        result = {
            "stdout": process.stdout,
            "stderr": process.stderr
        }
        connection.execute(text("UPDATE tasks SET status=:status, result=:result WHERE id=:id"),
                           {"status": "结束", "result": str(result), "id": task_id})


@app.post("/create_task")
async def create_task(data: CreateTaskData):
    with engine.connect() as connection:
        result = connection.execute(
            text("INSERT INTO tasks (script_path, script_args, status) VALUES (:script_path, :script_args, :status)"),
            {"script_path": data.script_path, "script_args": data.script_args, "status": "未开始"})
        task_id = result.lastrowid
    return {"task_id": task_id}


@app.post("/execute_task/{task_id}")
async def execute_task(task_id: int, background_tasks: BackgroundTasks):
    global task_lock
    with task_lock:
        with engine.connect() as connection:
            task_info = connection.execute(text("SELECT script_path, script_args, status FROM tasks WHERE id=:id"),
                                           {"id": task_id}).fetchone()

        if task_info and (task_info[2] == "未开始" or task_info[2] == "结束"):
            background_tasks.add_task(execute_task_in_subprocess, task_id, task_info[0], task_info[1])
            return {"message": "任务已放入后台执行"}
        else:
            return {"error": "任务不存在或已经在运行中"}


@app.get("/check_status/{task_id}")
async def check_status(task_id: int):
    with engine.connect() as connection:
        status = connection.execute(text("SELECT status FROM tasks WHERE id=:id"), {"id": task_id}).fetchone()

    if status:
        return {"status": status[0]}
    else:
        return {"error": "任务不存在"}


@app.get("/get_result/{task_id}")
async def get_result(task_id: int):
    with engine.connect() as connection:
        result = connection.execute(text("SELECT result FROM tasks WHERE id=:id"), {"id": task_id}).fetchone()

    if result:
        parsed_result = literal_eval(result[0])
        return {"result": parsed_result}
    else:
        return {"error": "任务不存在"}


@app.get("/get_all_tasks")
async def get_all_tasks():
    with engine.connect() as connection:
        task_result = connection.execute(text("SELECT id, script_path, script_args, status FROM tasks")).fetchall()

    all_tasks = []
    for task in task_result:
        all_tasks.append({
            "id": task[0],
            "script_path": task[1],
            "script_args": task[2],
            "status": task[3]
        })
    return all_tasks


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)