#!/usr/bin/env python3

import docker
import json
from datetime import datetime
from pathlib import Path
import pytz


def get_container_stats(container):
    try:
        stats = container.stats(stream=False)
        cpu_usage = stats["cpu_stats"]["cpu_usage"]["total_usage"]
        mem_usage = stats["memory_stats"]["usage"]
        return cpu_usage, mem_usage
    except Exception:
        return None, None


def main():
    client = docker.from_env()

    # Base folder of the project
    base_dir = Path(__file__).resolve().parent.parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Local timestamp (Netherlands)
    tz = pytz.timezone("Europe/Amsterdam")
    now_local = datetime.now(tz)

    data = {
        "timestamp": now_local.isoformat(),
        "containers": []
    }

    for container in client.containers.list(all=True):
        cpu, mem = get_container_stats(container)
        info = {
            "id": container.short_id,
            "name": container.name,
            "status": container.status,
            "image": container.image.tags[0] if container.image.tags else "unknown",
            "cpu_usage": cpu,
            "mem_usage": mem,
            "ports": container.attrs["NetworkSettings"]["Ports"]
        }
        data["containers"].append(info)

    # Local timestamp in filename
    filename = logs_dir / f"status_{now_local.strftime('%Y%m%d_%H%M%S')}.json"

    with filename.open("w") as f:
        json.dump(data, f, indent=4)

    print(f"✔ Status exported to: {filename}")


if __name__ == "__main__":
    main()
