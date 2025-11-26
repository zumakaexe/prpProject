#!/usr/bin/env python3

import docker
import json
import time
from datetime import datetime
from pathlib import Path
import pytz


def recreate_container(client, container):
    inspect = client.api.inspect_container(container.id)

    name = inspect["Name"].lstrip("/")
    image = inspect["Config"]["Image"]
    env = inspect["Config"].get("Env", [])

    # Ports
    ports_cfg = inspect["NetworkSettings"]["Ports"] or {}
    port_bindings = {}
    for port_proto, bindings in ports_cfg.items():
        if bindings:
            host_port = bindings[0]["HostPort"]
            port_bindings[port_proto] = host_port

    # Volumes
    mounts = inspect.get("Mounts", [])
    volume_bindings = {}
    for m in mounts:
        if m.get("Type") == "volume":
            volume_bindings[m["Name"]] = {
                "bind": m["Destination"],
                "mode": "rw" if m.get("RW", True) else "ro"
            }

    container.stop()
    container.remove()

    new_container = client.containers.run(
        image=image,
        name=name,
        detach=True,
        ports=port_bindings,
        volumes=volume_bindings,
        environment=env,
    )

    return new_container


def main():
    client = docker.from_env()

    base_dir = Path(__file__).resolve().parent.parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Netherlands local time
    tz = pytz.timezone("Europe/Amsterdam")
    now_local = datetime.now(tz)

    log_data = {
        "timestamp": now_local.isoformat(),
        "action": "update_containers",
        "results": []
    }

    containers = client.containers.list(all=True)

    for container in containers:
        if container.name.lower() == "portainer":
            continue

        image_tags = container.image.tags
        image = image_tags[0] if image_tags else None
        if not image:
            continue

        result = {
            "container": container.name,
            "old_image": image,
            "status": "",
            "duration_ms": 0
        }

        start_time = time.time()

        try:
            print(f"\n[INFO] Pulling latest image for {container.name} ({image})")
            client.images.pull(image)

            print(f"[INFO] Recreating container {container.name}")
            recreate_container(client, container)

            result["status"] = "success"

        except Exception as e:
            result["status"] = f"error: {e}"

        finally:
            result["duration_ms"] = int((time.time() - start_time) * 1000)
            log_data["results"].append(result)

    filename = logs_dir / f"update_{now_local.strftime('%Y%m%d_%H%M%S')}.json"
    with filename.open("w") as f:
        json.dump(log_data, f, indent=4)

    print(f"\n✔ Update results written to: {filename}")


if __name__ == "__main__":
    main()
