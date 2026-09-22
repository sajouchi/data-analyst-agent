import os
import tempfile

import re

import docker
from pathlib import Path

from loguru import logger

logger.remove()
logger.add("app\\logs\\run.log") # log file where logs will be added to

SANDBOX_DIR = Path(__file__).parent.resolve() # explicit path to locate Dockerfile

def set_sandbox_img():
    
    client = docker.from_env()
    try:
        image = client.images.get("agent-sandbox-container:early")
        print("image container exist!")
        logger.info("image container exist!")
        
        return True
        
    except docker.errors.ImageNotFound:
        print("image not found, building the image container....")
        logger.info("image not found, building the image container....")
        
        print("path = ",str(SANDBOX_DIR))
        logger.info("path = ",str(SANDBOX_DIR))
        
        image,log = client.images.build(
                                        path=str(SANDBOX_DIR),
                                        dockerfile="Dockerfile",
                                        tag="agent-sandbox-container:early",
                                        rm=True,)
        
        print(f"image built, image id = {image.id}")
        logger.info(f"image built, image id = {image.id}")
        
        return True

def gen_temp_file(agent_code:str) -> str:
    
    code_match = re.search(r"```python\s*\n(.*?)```", agent_code, re.DOTALL)
    
    if not code_match:
        print(">>> No Python code found in the response.")
        logger.info(">>> No Python code found in the response.")
        
        return False

    code_extracted = code_match.group(1)
    
    # isolated workspace folder for sandbox!
    sandbox_workspace = os.path.join(tempfile.gettempdir(),"sandbox_workspace")
    os.makedirs(sandbox_workspace,exist_ok=True)
    
    with tempfile.NamedTemporaryFile(mode="w",suffix=".py",
                                     delete=False, dir=sandbox_workspace) as tmpFile:
        
        tmpFile.write(code_extracted)
        temp_file_path = tmpFile.name
        
        print("temp file path is = ",temp_file_path)
        logger.info(f"temp file path is = {temp_file_path}")

    return temp_file_path

def execute_code(temp_file_path:str):
    
    client = docker.from_env()
        
    try:
        container = client.containers.run(
                            image='agent-sandbox-container:early',
                            command=f"python /app/{Path(temp_file_path).name}",
                            volumes={os.path.dirname(temp_file_path):{"bind": "/app","mode":"rw"}},
                            working_dir="/app",
                            #mem_limit="512m",       # Cap RAM usage to 512MB
                            #nano_cpus=1000000000,    # Cap CPU usage to 1 core
                            network_mode="none", # disables network access
                            remove=True)
        
        return container.decode("utf-8")
    except Exception as e:
        logger.info(f"failed running the container : {e}")
        return f"failed running the container : {e}"
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path) #  removes the pointer, used to delete the temp python file
        
