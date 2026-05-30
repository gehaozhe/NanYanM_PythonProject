from util.common import Database, get_timestamp
from util.download.task.info import TaskInfo

from pathlib import Path
from typing import List
import json
import os

class TaskDatabase(Database):
    def __init__(self):
        # 获取程序运行目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 向上三级到src目录
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        # 构建Loginformation文件夹路径
        loginformation_dir = os.path.join(src_dir, "Loginformation")
        # 构建数据库文件路径
        self.path = Path(loginformation_dir) / "task.db"
        # 确保目录存在
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.check_and_create_table()

    def check_and_create_table(self):
        self.execute_script("""
            PRAGMA journal_mode = WAL;
            CREATE TABLE IF NOT EXISTS "download_task" (
                "id"	INTEGER UNIQUE,
                "task_id"	TEXT UNIQUE,
                "cover_id"	TEXT,
                "title"	TEXT,
                "created_time"	INTEGER,
                "data"	TEXT,
                PRIMARY KEY("id" AUTOINCREMENT)
            );
            CREATE TABLE IF NOT EXISTS "completed_task" (
                "id"	INTEGER UNIQUE,
                "task_id"	TEXT UNIQUE,
                "cover_id"	TEXT,
                "title"	TEXT,
                "completed_time"	INTEGER,
                "data"	TEXT,
                PRIMARY KEY("id" AUTOINCREMENT)
            );""")
        
    def query_tasks(self, completed: bool = False):
        if completed:
            result = self.query("""
                SELECT data FROM completed_task
            """)
        else:
            result = self.query("""
                SELECT data FROM download_task
            """)

        return result

    def add_tasks(self, task_info_list: List[TaskInfo], completed: bool = False):
        # 通过 completed 参数来区分是插入到 download_task 还是 completed_task 表
        info_list = []

        for task_info in task_info_list:
            info_list.append((
                task_info.Basic.task_id,                                    # task_id
                task_info.Basic.cover_id,                                   # cover_id
                task_info.Basic.show_title,                                 # title
                get_timestamp(),                                            # created_time or completed_time
                json.dumps(task_info.to_dict(), ensure_ascii = False)       # data
            ))

        if completed:
            self.executemany("""
                INSERT INTO completed_task (task_id, cover_id, title, completed_time, data)
                VALUES (?, ?, ?, ?, ?)
            """, info_list)
        else:
            self.executemany("""
                INSERT INTO download_task (task_id, cover_id, title, created_time, data)
                VALUES (?, ?, ?, ?, ?)
            """, info_list)

    def update_task(self, task_info: TaskInfo):
        self.execute("""
            UPDATE download_task SET data = ? WHERE task_id = ?
        """, (json.dumps(task_info.to_dict(), ensure_ascii = False), task_info.Basic.task_id))

    def delete_task(self, task_id: str, completed: bool = False):
        if completed:
            self.execute("""
                DELETE FROM completed_task WHERE task_id = ?
            """, (task_id,))
        else:
            self.execute("""
                DELETE FROM download_task WHERE task_id = ?
            """, (task_id,))
