import subprocess
import time
import os

# Print output to log file
import sys
class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()
logfile = open('output.log', 'w')  # Open log file
sys.stdout = Tee(sys.stdout, logfile)  # Redirect concole to log

# List of Python script filenames to run sequentially
scripts = ["01_transcribe.py", "02_verbalize.py", "03_translate.py", "04_bigblocks.py"]

# Directory where the scripts are located (adjust if needed)
scripts_dir = "."

for script in scripts:
    script_path = os.path.join(scripts_dir, script)
    
    try:
        print(f"Starting script: {script}")
        start_time = time.time()
        
        # Run the script with Python 3 and wait for it to complete
        process = subprocess.Popen(["python3", script_path], cwd=scripts_dir)
        process.wait()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Script {script} completed in {elapsed_time:.2f} seconds.")
    
    except Exception as e:
        print(f"An error occurred while running {script}: {e}")
        break  # Stop execution if an error occurs

print("All scripts have finished running.")

logfile.close()  # Close log file
