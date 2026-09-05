import subprocess

def reset_pg_password():
    cmd = [
        r"C:\Program Files\PostgreSQL\18\bin\postgres.exe",
        "--single",
        "-D", r"C:\Program Files\PostgreSQL\18\data",
        "postgres"
    ]
    sql_commands = "ALTER USER postgres WITH PASSWORD '6769';\n"
    print("Setting PostgreSQL password for user 'postgres' to '6769'...")
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=sql_commands)
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    print("Return code:", proc.returncode)

if __name__ == "__main__":
    reset_pg_password()
