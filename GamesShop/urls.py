from django.conf.urls.static import static
from django.contrib import admin

from django.urls import path
from . import views, settings

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('signup/', views.SignUpView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),

    path('api/games/', views.api_games_list, name='api_games_list'),
    path('api/games/<int:game_id>/', views.api_game_detail, name='api_game_detail'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/profile/', views.api_user_profile, name='api_user_profile'),
    path('api/cart/add/', views.api_add_to_cart, name='api_add_to_cart'),
    path('api/cart/', views.api_cart_items, name='api_cart_items'),
    path('api/checkout/', views.api_checkout, name='api_checkout'),
    path('api/orders/', views.api_order_history, name='api_order_history'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile_edit/', views.profile_edit, name='edit_profile'),
    path('api/register/', views.api_register, name='api_register'),
    path('password_change/', views.password_change, name='password_change'),
    path('add_game/', views.admin_add_game, name='admin'),
    path('admin/', admin.site.urls),
    path('game/delete/<int:game_id>/', views.admin_delete_game, name='admin_delete_game'),
    path('cart/', views.cart_view, name='cart'),
    path('game/<int:game_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('profile/orders/', views.order_history, name='order_history'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('profile/clear-orders/<int:order_id>', views.delete_history, name='clear_history'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)