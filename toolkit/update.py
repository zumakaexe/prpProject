import subprocess
import datetime
import json
import os

LOGS_DIR = "logs"
CONTAINER_NAME = "cijferlijst"
IMAGE_NAME = "ezzoreon/cijferlijst:latest"
HOST_PORT = 80
CONTAINER_PORT = 5000


def run_cmd(cmd, ignore_errors=False):
    """
    Run a shell command and return (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0 and not ignore_errors:
            print(f"[ERROR] Command failed: {cmd}")
            print(result.stderr.strip())
        else:
            print(f"[OK] {cmd}")
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        print(f"[EXCEPTION] {cmd} -> {e}")
        if ignore_errors:
            return 0, "", str(e)
        else:
            return 1, "", str(e)


def update_cijferlijst():
    start_time = datetime.datetime.now()
    log_entry = {
        "task": "update_cijferlijst",
        "start_time": start_time.isoformat(),
        "steps": [],
        "final_status": "UNKNOWN"
    }

   
    cmd_pull = f"docker pull {IMAGE_NAME}"
    rc, out, err = run_cmd(cmd_pull)
    log_entry["steps"].append({
        "step": "docker_pull",
        "command": cmd_pull,
        "returncode": rc,
        "stdout": out,
        "stderr": err
    })
    if rc != 0:
        log_entry["final_status"] = "FAILED_PULL"
        return log_entry

  
    cmd_stop = f"docker stop {CONTAINER_NAME}"
    rc, out, err = run_cmd(cmd_stop, ignore_errors=True)
    log_entry["steps"].append({
        "step": "docker_stop",
        "command": cmd_stop,
        "returncode": rc,
        "stdout": out,
        "stderr": err
    })


    cmd_rm = f"docker rm {CONTAINER_NAME}"
    rc, out, err = run_cmd(cmd_rm, ignore_errors=True)
    log_entry["steps"].append({
        "step": "docker_rm",
        "command": cmd_rm,
        "returncode": rc,
        "stdout": out,
        "stderr": err
    })

    
    cmd_run = (
        f"docker run -d --name {CONTAINER_NAME} "
        f"-p {HOST_PORT}:{CONTAINER_PORT} "
        f"{IMAGE_NAME}"
    )
    rc, out, err = run_cmd(cmd_run)
    log_entry["steps"].append({
        "step": "docker_run",
        "command": cmd_run,
        "returncode": rc,
        "stdout": out,
        "stderr": err
    })

    if rc == 0:
        log_entry["final_status"] = "SUCCESS"
        log_entry["new_container_id"] = out.strip()
    else:
        log_entry["final_status"] = "FAILED_RUN"

    end_time = datetime.datetime.now()
    log_entry["end_time"] = end_time.isoformat()
    log_entry["duration_seconds"] = (end_time - start_time).total_seconds()

    return log_entry


def save_log(entry):
    os.makedirs(LOGS_DIR, exist_ok=True)
    now = datetime.datetime.now()
    filename = os.path.join(
        LOGS_DIR,
        f"update_{now.strftime('%Y%m%d-%H%M%S')}.json"
    )
    with open(filename, "w") as f:
        json.dump(entry, f, indent=4)

    print(f"[UPDATE] Log saved → {filename}")


if __name__ == "__main__":
    print("[UPDATE] Starting cijferlijst update...")
    result = update_cijferlijst()
    save_log(result)
    print(f"[UPDATE] Final status: {result['final_status']}")
