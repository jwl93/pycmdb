"""
Web 界面模块 - 提供可视化的 CMDB 操作界面
"""
import json
import os
import threading
import subprocess
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS

from scripts.detector import detect_changes, scan_all_configs, ChangeType
from scripts.validator import validate_change
from scripts.lock import DeployLock

app = Flask(__name__, template_folder="templates")
CORS(app)

# 全局日志存储
logs = []
log_lock = threading.Lock()


def add_log(level: str, message: str):
    """添加日志"""
    import datetime
    with log_lock:
        logs.append({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        })
        # 只保留最近 100 条
        if len(logs) > 100:
            logs.pop(0)


def run_command(cmd: list[str]) -> tuple[int, str]:
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "命令执行超时"
    except Exception as e:
        return 1, str(e)


@app.route("/")
def index():
    """主页"""
    return render_template("index.html")


@app.route("/api/changes")
def api_changes():
    """获取检测到的变更"""
    changes = detect_changes()
    return jsonify({
        "count": len(changes),
        "changes": [
            {
                "config_type": c.config_type.value,
                "change_type": c.change_type.value,
                "name": c.name,
            }
            for c in changes
        ]
    })


@app.route("/api/validate", methods=["POST"])
def api_validate():
    """校验变更"""
    data = request.get_json() or {}
    all_configs = data.get("all", False)

    add_log("INFO", f"开始校验 (all={all_configs})...")

    if all_configs:
        changes = scan_all_configs()
    else:
        changes = detect_changes()

    results = []
    for c in changes:
        valid, errors = validate_change(c)
        results.append({
            "config_type": c.config_type.value,
            "name": c.name,
            "valid": valid,
            "errors": errors,
        })
        status = "OK" if valid else "FAIL"
        add_log("INFO" if valid else "ERROR", f"[{status}] {c.config_type.value}/{c.name}")

    all_valid = all(r["valid"] for r in results)
    add_log("INFO" if all_valid else "ERROR", f"校验{'通过' if all_valid else '失败'}")

    return jsonify({
        "total": len(results),
        "valid": all_valid,
        "results": results,
    })


@app.route("/api/deploy", methods=["POST"])
def api_deploy():
    """执行部署"""
    data = request.get_json() or {}
    config_type = data.get("type")
    targets = data.get("targets")

    add_log("INFO", f"开始部署 (type={config_type}, targets={targets})...")

    # 检查锁
    lock = DeployLock()
    acquired, msg = lock.acquire()
    if not acquired:
        add_log("ERROR", f"部署被锁定: {msg}")
        return jsonify({"success": False, "error": msg}), 409

    try:
        changes = detect_changes()

        # 过滤
        if config_type:
            changes = [c for c in changes if c.config_type.value == config_type]
        if targets:
            target_list = [t.strip() for t in targets.split(",")]
            changes = [c for c in changes if c.name in target_list]

        if not changes:
            add_log("WARN", "没有可部署的变更")
            return jsonify({"success": False, "error": "没有可部署的变更"})

        # 校验
        for c in changes:
            valid, errors = validate_change(c)
            if not valid:
                add_log("ERROR", f"校验失败: {c.config_type.value}/{c.name}")
                return jsonify({
                    "success": False,
                    "error": f"校验失败: {c.config_type.value}/{c.name}",
                    "details": errors,
                })

        # 执行
        results = {"success": 0, "failed": 0, "details": []}
        for c in changes:
            add_log("INFO", f"执行: {c.config_type.value}/{c.name} ({c.change_type.value})")
            results["details"].append({
                "name": c.name,
                "type": c.config_type.value,
                "event": c.change_type.value,
            })
            results["success"] += 1

        add_log("INFO", f"部署完成: {results['success']} 成功, {results['failed']} 失败")

        return jsonify({
            "success": True,
            "results": results,
        })

    finally:
        lock.release()


@app.route("/api/logs")
def api_logs():
    """获取日志流"""
    def generate():
        last_count = 0
        while True:
            with log_lock:
                if len(logs) > last_count:
                    for log in logs[last_count:]:
                        yield f"data: {json.dumps(log)}\n\n"
                    last_count = len(logs)
            import time
            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/logs/latest")
def api_logs_latest():
    """获取最新日志"""
    with log_lock:
        return jsonify(logs[-20:] if logs else [])


def main():
    port = int(os.environ.get("PORT", 5000))
    add_log("INFO", f"CMDB Web 服务启动在 http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
