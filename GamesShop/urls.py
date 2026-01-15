from django.conf.urls.static import static
from django.contrib import admin

from django.urls import path
from . import views, settings

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('signup/', views.SignUpView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile_edit/', views.profile_edit, name='edit_profile'),
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