from quart import Blueprint, Response


healthcheckb = Blueprint('health_check', __name__, )


@healthcheckb.route('/manage/health', methods=['GET'])
async def health_check() -> Response:
    return Response(
        status=200
    )