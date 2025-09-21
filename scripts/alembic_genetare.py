import subprocess

def run_command(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print("Output:", result.stdout)
    if result.stderr:
        print("Error:", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}")

def main():
    update = input("Введите название обновления: ")
    commands_in_container = [
        f"alembic revision --autogenerate -m \"{update}\"",
        "alembic upgrade head"
    ]

    for cmd in commands_in_container:
        docker_command = f"docker-compose exec app {cmd}"
        run_command(docker_command)

    run_command("docker-compose down")
    run_command("docker-compose up -d")

if __name__ == "__main__":
    main()
