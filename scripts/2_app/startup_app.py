import subprocess
import os

root_dir = "/home/cdsw/rag-studio" if os.getenv("IS_COMPOSABLE", "") != "" else "/home/cdsw"
os.chdir(root_dir)

while True:
    print(subprocess.run(["bash scripts/startup_app.sh"], shell=True))
    print("Application Restarting")
