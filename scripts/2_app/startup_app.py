# import subprocess
# import os

# root_dir = "/home/cdsw"
# os.chdir(root_dir)

# while True:
#     print(subprocess.run(["bash scripts/startup_app.sh"], shell=True))
#     print("Application Restarting")

import subprocess
import os
import time

root_dir = "/home/cdsw"
os.chdir(root_dir)

while True:
    try:
        # Option B: using a list without shell=True (preferred)
        result = subprocess.run(["bash", "scripts/2_app/startup_app.sh"])
        
        if result.returncode == 0:
            print("Application exited successfully.")
        else:
            print(f"Application crashed with exit code {result.returncode}. Restarting...")
    except Exception as e:
        print(f"Error occurred: {e}. Restarting...")

    print("Application Restarting in 5 seconds...")
    time.sleep(5)
