"""
Deploy 锁 - 防止并发执行导致冲突
"""
import os
import time
import fcntl
from pathlib import Path
from datetime import datetime

from scripts import get_cmdb_root


class DeployLock:
    """
    文件锁实现，确保同一时间只有一个 deploy 执行
    """

    LOCK_FILE = ".deploy.lock"

    def __init__(self, timeout: int = 0):
        """
        timeout: 等待锁的最大秒数，0 表示不等待
        """
        self.timeout = timeout
        self.lock_path = get_cmdb_root() / self.LOCK_FILE
        self.fd = None
        self.acquired = False

    def acquire(self) -> tuple[bool, str]:
        """
        尝试获取锁
        返回 (成功标志, 消息)
        """
        # 确保锁目录存在
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查是否存在旧锁
        if self.lock_path.exists():
            if self._is_stale_lock():
                self._remove_lock()
            else:
                # 锁存在且活跃，检查持有者信息
                info = self._read_lock_info()
                return False, f"部署正在进行中 (PID: {info.get('pid', 'unknown')}, 开始时间: {info.get('time', 'unknown')})"

        try:
            self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR)
            # 非阻塞锁
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # 写入锁信息
            self._write_lock_info()

            self.acquired = True
            return True, "OK"

        except OSError:
            # 锁被占用
            return False, self._get_lock_holder_info()

    def _is_stale_lock(self) -> bool:
        """检查锁是否过期（进程已死）"""
        info = self._read_lock_info()
        if not info:
            return True

        pid = info.get("pid")
        if pid and not self._process_exists(pid):
            return True

        # 锁超过 30 分钟自动过期（防止极端情况）
        lock_time = info.get("time", "")
        if lock_time:
            try:
                dt = datetime.fromisoformat(lock_time)
                elapsed = (datetime.now() - dt).total_seconds()
                if elapsed > 1800:
                    return True
            except Exception:
                pass

        return False

    def _process_exists(self, pid: int) -> bool:
        """检查进程是否存在"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _read_lock_info(self) -> dict:
        """读取锁文件信息"""
        try:
            with open(self.lock_path) as f:
                import json
                return json.load(f)
        except Exception:
            return {}

    def _write_lock_info(self):
        """写入锁文件信息"""
        import json
        info = {
            "pid": os.getpid(),
            "time": datetime.now().isoformat(),
            "host": os.environ.get("HOSTNAME", "unknown"),
        }
        os.ftruncate(self.fd, 0)
        os.lseek(self.fd, 0, os.SEEK_SET)
        os.write(self.fd, json.dumps(info, indent=2).encode())

    def _get_lock_holder_info(self) -> str:
        """获取当前锁持有者信息"""
        info = self._read_lock_info()
        if info:
            return f"部署正在进行中 (PID: {info.get('pid', 'unknown')}, 开始时间: {info.get('time', 'unknown')})"
        return "部署正在进行中"

    def _remove_lock(self):
        """删除锁文件"""
        try:
            self.lock_path.unlink()
        except Exception:
            pass

    def release(self):
        """释放锁"""
        if self.acquired and self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                os.close(self.fd)
            except Exception:
                pass
            self.acquired = False

        if self.lock_path.exists():
            self._remove_lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def acquire_deploy_lock(timeout: int = 0) -> tuple[bool, str]:
    """
    获取部署锁
    返回 (成功, 消息)
    """
    lock = DeployLock(timeout=timeout)
    return lock.acquire()


def release_deploy_lock():
    """释放部署锁（一般由 DeployLock 上下文管理器自动处理）"""
    pass
