import os
import tempfile

import re

import docker
from pathlib import Path

from loguru import logger

logger.add("app\\logs\\run.log") # log file where logs will be added to
SANDBOX_DIR = Path(__file__).parent.resolve() # explicit path to locate Dockerfile

def set_sandbox_img():
    
    client = docker.from_env()
    try:
        image = client.images.get("agent-sandbox-container:early")
        print("image container exist!")
        
        return True
        
    except docker.errors.ImageNotFound:
        print("image not found, building the image container....")
        print("path = ",str(SANDBOX_DIR))
        image,log = client.images.build(
                                        path=str(SANDBOX_DIR),
                                        dockerfile="Dockerfile",
                                        tag="agent-sandbox-container:early",
                                        rm=True,)
        
        print(f"image built, image id = {image.id}")
        return True

def gen_temp_file(agent_code:str) -> str:
    
    code_match = re.search(r"```python\s*\n(.*?)```", agent_code, re.DOTALL)
    
    if not code_match:
        print(">>> No Python code found in the response.")
        return False

    code_extracted = code_match.group(1)
    
    with tempfile.NamedTemporaryFile(mode="w",suffix=".py",delete=False) as tmpFile:
        tmpFile.write(code_extracted)
        temp_file_path = tmpFile.name
        
        print("temp file path is = ",temp_file_path)

    return temp_file_path

def execute_code(temp_file_path:str):
    
    client = docker.from_env()
        
    try:
        container = client.containers.run(
                            image='agent-sandbox-container:early',
                            command=f"python /app/{Path(temp_file_path).name}",
                            volumes={os.path.dirname(temp_file_path):{"bind": "/app","mode":"rw"}},
                            working_dir="/app",
                            remove=True)
        
        return container.decode("utf-8")
    except Exception as e:
        return f"failed running the container : {e}"
    finally:
        os.unlink(temp_file_path) #  removes the pointer, used to delete the temp python file
        
