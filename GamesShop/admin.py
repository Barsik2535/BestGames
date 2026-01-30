from django.contrib import admin
from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'genre', 'developer', 'price', 'is_active', 'created_at']
    list_filter = ['genre', 'is_active', 'created_at']
    search_fields = ['title', 'developer']
    list_editable = ['is_active', 'price']
    readonly_fields = ['created_at']