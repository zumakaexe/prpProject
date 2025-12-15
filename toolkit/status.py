import docker
import json
import datetime
import os

LOGS_DIR = "logs"
TARGET_CONTAINER = "cijferlijst"


def get_container_status():
    client = docker.from_env()
    containers = client.containers.list(all=True)

    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "containers": []
    }

    for c in containers:
        info = {
            "id": c.id[:12],
            "name": c.name,
            "image": c.image.tags,
            "status": c.status,
            "created": c.attrs.get("Created"),
            "ports": c.attrs.get("NetworkSettings", {}).get("Ports", {})
        }

 
        health = c.attrs.get("State", {}).get("Health")
        if health:
            info["health"] = health.get("Status")
        else:
            info["health"] = "no healthcheck"


        info["is_cijferlijst"] = (c.name == TARGET_CONTAINER)

        data["containers"].append(info)

    return data


def save_to_json(data):
    os.makedirs(LOGS_DIR, exist_ok=True)
    now = datetime.datetime.now()
    filename = os.path.join(
        LOGS_DIR,
        f"status_{now.strftime('%Y%m%d-%H%M%S')}.json"
    )
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[STATUS] Log saved → {filename}")


def print_summary(data):
    print("\n=== CONTAINER STATUS SUMMARY ===")
    for c in data["containers"]:
        mark = "[TARGET]" if c["is_cijferlijst"] else "        "
        print(
            f"{mark} {c['name']:<15} "
            f"status={c['status']:<10} "
            f"health={c['health']}"
        )


if __name__ == "__main__":
    print("[STATUS] Collecting container information...")
    status_data = get_container_status()
    save_to_json(status_data)
    print_summary(status_data)
