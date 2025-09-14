#!/usr/bin/env python3
import subprocess
import time
import sys
from pathlib import Path


def start_service(name, cmd, cwd=None):
    print(f"Starting {name}...")
    return subprocess.Popen(cmd, shell=True, cwd=cwd)


def main():
    processes = []

    try:
        # Start Temporal server
        processes.append(start_service(
            "Temporal Server",
            "temporal server start-dev"
        ))


        # Start frontend (if you have it)
        # processes.append(start_service(
        #     "Vue Frontend",
        #     "npm run dev",
        #     cwd="frontend"
        # ))

        print("\n✅ All services started!")
        print("📊 Neo4j: http://localhost:7474")
        print("⏱️  Temporal UI: http://localhost:8233")
        print("\nPress Ctrl+C to stop all services...")

        # Wait for keyboard interrupt
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for p in processes:
            p.terminate()


if __name__ == "__main__":
    main()
