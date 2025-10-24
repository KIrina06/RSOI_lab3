from peewee import *
from .base_model import BaseModel


class CarsModel(BaseModel):
    id = IdentityField()
    car_uid = UUIDField(unique=True, null=False)
    brand = CharField(max_length=80, null=False)
    model = CharField(max_length=80, null=False)
    registration_number = CharField(max_length=20, null=False)
    power = IntegerField()
    price = IntegerField(null=False)
    availability = BooleanField(null=False)
    type = CharField(max_length=20, constraints=[Check("type IN ('SEDAN', 'SUV', 'MINIVAN', 'ROADSTER')")])

    def to_dict(self):
        return {
            "carUid": str(self.car_uid),
            "brand": str(self.brand),
            "model": str(self.model),
            "registrationNumber": str(self.registration_number),
            "power": self.power,
            "type": str(self.type),
            "price": self.price,
            "available": bool(self.availability)
        }

    class Meta:
        db_table = "cars"
