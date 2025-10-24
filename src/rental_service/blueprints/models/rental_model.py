from peewee import *
from .base_model import BaseModel


class RentalModel(BaseModel):
    id = IdentityField()
    rental_uid = UUIDField(unique=True, null=False)
    username = CharField(max_length=80, null=False)
    payment_uid = UUIDField(null=False)
    car_uid = UUIDField(null=False)
    date_from = DateField(null=False, formats='%Y-%m-%d')
    date_to = DateField(null=False, formats='%Y-%m-%d')
    status = CharField(max_length=20, constraints=[Check("status IN ('IN_PROGRESS', 'FINISHED', 'CANCELED')")])

    def to_dict(self):
        return {
            "rentalUid": str(self.rental_uid),
            "username": str(self.username),
            "paymentUid": str(self.payment_uid),
            "carUid": str(self.car_uid),
            "dateFrom": str(self.date_from),
            "dateTo": str(self.date_to),
            "status": str(self.status)
        }

    class Meta:
        db_table = "rental"
