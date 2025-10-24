from peewee import *
from .base_model import BaseModel


class PaymentModel(BaseModel):
    id = IdentityField()
    payment_uid = UUIDField(null=False)
    status = CharField(max_length=20, constraints=[Check("status IN ('PAID', 'CANCELED')")])
    price = IntegerField(null=False)

    def to_dict(self):
        return {
            "paymentUid": str(self.payment_uid),
            "status": str(self.status),
            "price": self.price,
        }

    class Meta:
        db_table = "payment"
