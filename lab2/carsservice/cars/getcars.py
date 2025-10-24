import json
from quart import Blueprint, Response, request
from .models.modelc import CarsModel

getcarsb = Blueprint('get_cars', __name__, )


def validate_args(args):
    errors = []
    if 'page' in args.keys():
        try:
            page = int(args['page'])
            if page <= 0:
                errors.append('wrong page number')
        except ValueError:
            errors.append('page should be a number')
            page = None
    else:
        errors.append('enter page number')
        page = None

    if 'size' in args.keys():
        try:
            size = int(args['size'])
            if size <= 0:
                errors.append('wrong size number')
        except ValueError:
            size = None
            errors.append('Size should be a number')
    else:
        errors.append('enter size number')
        size = None

    if 'showAll' in args.keys():
        if args['showAll'].lower() == 'true':
            show_all = True
        elif args['showAll'].lower() == 'false':
            show_all = False
        else:
            errors.append('showAll must be true or false')
            show_all = None
    else:
        show_all = False

    return page, size, show_all, errors


@getcarsb.route('/api/v1/cars/', methods=['GET'])
async def get_cars() -> Response:
    page, size, show_all, errors = validate_args(request.args)

    if len(errors) > 0:
        return Response(
            status=400,
            content_type='application/json',
            response=json.dumps({
                'errors': errors
            })
        )

    if not show_all:
        query = CarsModel.select().where(CarsModel.availability == True)
        count_total = query.count()
        cars = [car.to_dict() for car in query.paginate(page, size)]
    else:
        count_total = CarsModel.select().count()
        cars = [car.to_dict() for car in CarsModel.select().paginate(page, size)]

    return Response(
        status=200,
        content_type='application/json',
        response=json.dumps({
          "page": page,
          "pageSize": size,
          "totalElements": count_total,
          "items": cars
        })
    )
