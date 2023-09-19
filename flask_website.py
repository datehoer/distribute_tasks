import uvicorn
import subprocess
import threading
import psutil
from typing import List
from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from ast import literal_eval
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
engine = create_engine('sqlite:///tasks.db', connect_args={"check_same_thread": False}, echo=True, pool_size=10, max_overflow=20)
task_lock = threading.Lock()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源。在生产环境中，你应该设置特定的来源。
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class CreateTaskData(BaseModel):
    script_path: str
    script_args: str


with engine.connect() as connection:
    trans = connection.begin()
    connection.execute(text('''CREATE TABLE IF NOT EXISTS tasks
                               (id INTEGER PRIMARY KEY,
                               script_path TEXT,
                               script_args TEXT,
                               status TEXT,
                               result TEXT,
                               subprocess_pid INTEGER)'''))
    trans.commit()
    trans.close()


def execute_task_in_subprocess(task_id, script_path, script_args):
    try:
        with engine.connect() as conn:
            tran = conn.begin()
            conn.execute(text("UPDATE tasks SET status=:status, `result` = NULL WHERE id=:id"),
                         {"status": "进行中", "subprocess_pid": None, "id": task_id})
            tran.commit()
            tran.close()
        process = subprocess.Popen(
            ["python", script_path, script_args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        subprocess_pid = process.pid
        with engine.connect() as conn:
            tran = conn.begin()
            conn.execute(text("UPDATE tasks SET subprocess_pid=:subprocess_pid WHERE id=:id"),
                         {"subprocess_pid": subprocess_pid, "id": task_id})
            tran.commit()
            tran.close()
        process.wait()
        stdout_data, stderr_data = process.communicate()
        result = {
            "stdout": str(stdout_data),
            "stderr": str(stderr_data)
        }
        with engine.connect() as conn:
            tran = conn.begin()
            conn.execute(text("UPDATE tasks SET status=:status, result=:result,subprocess_pid = NULL  WHERE id=:id"),
                         {"status": "结束", "result": str(result), "id": task_id})
            tran.commit()
            tran.close()
    except Exception as e:
        error_message = str(e)
        with engine.connect() as conn:
            tran = conn.begin()
            conn.execute(text("UPDATE tasks SET status=:status, result=:error_message,subprocess_pid = NULL WHERE id=:id"),
                         {"status": "失败", "error_message": str({"stdout": "", "stderr": error_message}), "id": task_id})
            tran.commit()
            tran.close()


def get_process_status(pid):
    try:
        process = psutil.Process(pid)
        return {"code": 0, "message": process.status(), "status": "进行中"}
    except psutil.NoSuchProcess:
        return {"code": 1, "message": "进程不存在", "status": "结束"}
    except Exception as e:
        return {"code": 2, "message": f"未知错误: {str(e)}", "status": "错误"}


@app.post("/execute_selected_tasks")
async def execute_selected_tasks(task_ids: dict, background_tasks: BackgroundTasks):
    global task_lock
    for task_id in task_ids['task_ids']:
        with task_lock:
            with engine.connect() as conn:
                tran = conn.begin()
                task_info = conn.execute(
                    text("SELECT script_path, script_args, status FROM tasks WHERE id=:id"),
                    {"id": task_id}
                ).fetchone()
                tran.commit()
                tran.close()
            if task_info and (task_info[2] == "未开始" or task_info[2] == "结束"):
                background_tasks.add_task(execute_task_in_subprocess, task_id, task_info[0], task_info[1])

    return {"message": "选中的任务已放入后台执行"}


@app.post("/delete_selected_tasks")
async def delete_selected_tasks(task_ids: dict):
    with engine.connect() as conn:
        for task_id in task_ids['task_ids']:
            tran = conn.begin()
            conn.execute(text("DELETE FROM tasks WHERE id=:id"), {"id": task_id})
            tran.commit()

    return {"message": "选中的任务已删除"}


@app.post("/create_task")
async def create_task(data: CreateTaskData):
    data_spilt = data.script_args.split("|")
    task = []
    for i in data_spilt:
        if i == "":
            continue
        with engine.connect() as conn:
            tran = conn.begin()
            result = conn.execute(
                text("INSERT INTO tasks (script_path, script_args, status) VALUES (:script_path, :script_args, :status)"),
                {"script_path": data.script_path, "script_args": i, "status": "未开始"})
            tran.commit()
            tran.close()
            task_id = result.lastrowid
            task.append({'task_id': task_id, "task_keyword": i})
    return task


@app.post("/execute_task/{task_id}")
async def execute_task(task_id: int, background_tasks: BackgroundTasks):
    global task_lock
    with task_lock:
        with engine.connect() as conn:
            tran = conn.begin()
            task_info = conn.execute(text("SELECT script_path, script_args, status FROM tasks WHERE id=:id"),
                                           {"id": task_id}).fetchone()
            tran.commit()
            tran.close()
        if task_info and (task_info[2] == "未开始" or task_info[2] == "结束" or task_info[2] == "失败"):
            background_tasks.add_task(execute_task_in_subprocess, task_id, task_info[0], task_info[1])
            return {"message": "任务已放入后台执行"}
        else:
            return {"error": "任务不存在或已经在运行中"}


@app.get("/check_status/{task_id}")
async def check_status(task_id: int):
    with engine.connect() as conn:
        tran = conn.begin()
        status = conn.execute(text("SELECT status, subprocess_pid FROM tasks WHERE id=:id"), {"id": task_id}).fetchone()
        tran.commit()
        tran.close()
        task_status = status[0]
        subprocess_pid = status[1]
    if task_status == "进行中":
        if subprocess_pid is not None:
            process_status = get_process_status(subprocess_pid)
            with engine.connect() as conn:
                tran = conn.begin()
                conn.execute(text("UPDATE tasks SET status=:status, result=:result WHERE id=:id"),
                             {"status": process_status["status"], "result": {'stdout': process_status["message"], "stderr": ""}, "id": task_id})
                tran.commit()
                tran.close()
            if process_status["code"] == 0:
                return {"status": process_status["status"]}
            else:
                return {"status": process_status["status"]}
    if status:
        return {"status": status[0]}
    else:
        return {"error": "任务不存在"}


@app.get("/get_result/{task_id}")
async def get_result(task_id: int):
    with engine.connect() as conn:
        tran = conn.begin()
        result = conn.execute(text("SELECT result, subprocess_pid FROM tasks WHERE id=:id"), {"id": task_id}).fetchone()
        tran.commit()
        tran.close()
        task_status = result[0]
        subprocess_pid = result[1]
    if task_status is not None:
        parsed_result = literal_eval(task_status)
        if task_status == "进行中" and subprocess_pid is not None:
            process_status = get_process_status(subprocess_pid)
            with engine.connect() as conn:
                tran = conn.begin()
                conn.execute(text("UPDATE tasks SET status=:status, result=:result WHERE id=:id"),
                             {"status": process_status["status"],
                              "result": {'stdout': process_status["message"], "stderr": ""}, "id": task_id})
                tran.commit()
                tran.close()
            if process_status["code"] == 0:
                return {"status": process_status["status"], "result": {'stdout': process_status["message"], "stderr": ""}}
            else:
                return {"status": process_status["status"], "result": {"stderr": "任务未开始/不存在"}}
        return {"result": parsed_result}
    else:
        return {"result": {"stderr": "任务未开始/不存在"}}


@app.get("/get_all_tasks")
async def get_all_tasks():
    with engine.connect() as conn:
        tran = conn.begin()
        task_result = conn.execute(text("SELECT id, script_path, script_args, status, subprocess_pid FROM tasks")).fetchall()
        tran.commit()
        tran.close()
    all_tasks = []
    for task in task_result:
        task_status = task[3]
        subprocess_pid = task[4]
        if subprocess_pid is not None:
            process_status = get_process_status(subprocess_pid)
            if process_status["code"] == 0:
                task_status = process_status["status"]
                with engine.connect() as conn:
                    tran = conn.begin()
                    conn.execute(text("UPDATE tasks SET status=:status, result=:result WHERE id=:id"),
                                 {"status": process_status["status"],
                                  "result": {'stdout': process_status["message"], "stderr": ""}, "id": task[0]})
                    tran.commit()
                    tran.close()
            else:
                task_status = process_status["status"]
        all_tasks.append({
            "id": task[0],
            "script_path": task[1],
            "script_args": task[2],
            "status": task_status
        })
    return all_tasks


@app.get("/delete_task/{task_id}")
async def delete_task(task_id: int):
    with engine.connect() as conn:
        tran = conn.begin()
        conn.execute(text("DELETE FROM tasks WHERE id=:id"), {"id": task_id})
        tran.commit()
        tran.close()
    return {"message": "任务已删除"}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
