import environ
import requests

def get_batch_task_metadata():
    env = environ.Env()
    uri = env.str("ECS_CONTAINER_METADATA_URI_V4", None)
    if not uri:
        return {}
    
    end_point = uri + "/task"
    response = requests.get(end_point)
    return response
