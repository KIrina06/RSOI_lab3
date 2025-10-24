import os
import json
import time

from quart import Blueprint, Response, request
from queue_service.service_requests import delete_data_from_service


post_command_blueprint = Blueprint('post_command', __name__, )


@post_command_blueprint.route('/api/v1/command_delete', methods=['POST'])
async def post_command() -> Response:
    data = await request.body
    command = json.loads(data)
    response = delete_data_from_service(command['url'], command['headers'], timeout=10)
    while response is None:
        time.sleep(10)
        response = delete_data_from_service(
            command['url'], command['headers'], timeout=10)
    return Response(
        status=200
    )