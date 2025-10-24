from quart import Blueprint, Response


health_check_blueprint = Blueprint('health_check', __name__, )


@health_check_blueprint.route('/manage/health', methods=['GET'])
async def health_check() -> Response:
    return Response(
        status=200
    )