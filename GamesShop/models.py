from enum import unique

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email=self.normalize_email(email)
        user=self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email=models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    objects=CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    def __str__(self):
        return self.email
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email
    def get_short_name(self):
        return self.first_name  or self.email
class Game(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=255)
    image=models.ImageField(upload_to='games/', null=True, blank=True)
    developer = models.CharField(max_length=255)
    description=models.TextField(blank=True)
    price=models.DecimalField(decimal_places=2, max_digits=10)
    created_at=models.DateTimeField(default=timezone.now)
    is_active=models.BooleanField(default=True)
    class Meta:
        verbose_name_plural = 'Игры'
        verbose_name = 'Игры'
        ordering=['-created_at',]
    def __str__(self):
        return self.title
class CartGame(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    game=models.ForeignKey(Game,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    added_at=models.DateTimeField(default=timezone.now)
    class Meta:
        unique_together = ('user', 'game')
    def __str__(self):
        return f"{self.game.title} * {self.quantity}"
    @property
    def total_price(self):
        return self.quantity * self.game.price
class Order(models.Model):
    STATUS_CHOICES = (
         ('pending','Ожидает оплаты'),
         ('paid','Оплачено'),
         ('canceled', 'Отменено')
    )
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20, choices=STATUS_CHOICES,default='pending')
    total_amount=models.DecimalField(decimal_places=2, max_digits=10,default=0)
    class Meta:
        ordering=['-created_at']
    def __str__(self):
        return f'{self.id} - {self.user.email}'
    def calculate_total_amount(self):
        self.total_amount=sum(item.subtotal for item in self.items.all())
        self.save(update_fields=['total_amount'])
class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    game=models.ForeignKey(Game,on_delete=models.CASCADE)
    price_at_purchase=models.DecimalField(decimal_places=2, max_digits=10,default=0)
    quantity=models.PositiveIntegerField(default=1)
    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity
    def __str__(self):
        return f"{self.game.title} * {self.price_at_purchase}"


