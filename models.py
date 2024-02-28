# models.py
from tortoise import fields, models

class LotteryTicket(models.Model):
    id = fields.IntField(pk=True)
    ticket_code = fields.CharField(max_length=50, unique=True)
    result = fields.CharField(max_length=50, null=True)
    used = fields.BooleanField(default=False)
    use_count = fields.IntField(default=0)  # æ°å¢å­æ®µï¼è¡¨ç¤ºä½¿ç¨æ¬¡æ°

class AdminUser(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=20, unique=True)
    password = fields.CharField(max_length=128)  # ç´æ¥å­å¨ææå¯ç 

    @classmethod
    async def create_admin(cls):
        username = "saaduu123"
        password = "saaduu@123"
        existing_user = await cls.get_or_none(username=username)
        if existing_user is None:
            # ç´æ¥å­å¨ææå¯ç 
            user = cls(username=username, password=password)
            print("åå»ºè´¦å·å¯ç æåï¼")
            await user.save()

    def verify_password(self, password):
        # ç´æ¥æ¯è¾ææå¯ç 
        return self.password == password
