import subprocess


def main():
    print("Hello from automate CLI!")

def serve():
    subprocess.run([
        "gunicorn",
        "automate.main:app",
        "--workers", "4",
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--bind", "0.0.0.0:8000"
    ])