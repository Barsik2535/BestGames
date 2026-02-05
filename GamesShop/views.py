
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView, TemplateView
from django.contrib.auth import update_session_auth_hash
from GamesShop.forms import CustomUserCreationForm, LoginForm, ProfileEditForm, PasswordChangeForm, GameAddForm
from GamesShop.models import Game, CartGame, Order, OrderItem
from django.db import IntegrityError
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


class HomeView(TemplateView):
    template_name = 'index.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games']=Game.objects.filter(is_active=True).order_by('-created_at')[:12]
        return context

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name= 'register.html'
    success_url = reverse_lazy('login')
    def form_valid(self, form):
        response=super().form_valid(form)
        messages.success(self.request, 'Thank you for signing up!')
        return response
class LoginView(View):
    form_class=LoginForm
    template_name = 'login.html'
    def get(self, request):
        form =self.form_class()
        return render(request, self.template_name, {'form': form})
    def post(self, request):
        form=self.form_class(request.POST)
        if form.is_valid():
            email=form.cleaned_data.get('email')
            password=form.cleaned_data.get('password')

            user = authenticate(username=email, password=password)
            if user is not None:
                login(request,user)
                messages.success(request, f'Hello,{user.get_short_name()}!')
                return redirect('home')
            else:
                print('FAIL')
                messages.error(request, 'Please enter a correct email and password.')
        return render(request,self.template_name,{'form': form})


def logout_view(request):
        logout(request)
        messages.success(request, 'You have been logged out!')
        return redirect('home')
class ProfileView(TemplateView):
    template_name='profile.html'
    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        return context
@login_required
def profile_edit(request):
    if request.method == 'POST':
        form= ProfileEditForm(request.POST,instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please enter a correct email and password.')
    else:
        form= ProfileEditForm(instance=request.user)
    context= {
        'form': form,
        'user': request.user
    }
    return render(request, 'profile_edit.html', context)
@login_required
def password_change(request):
    if request.method == 'POST':
        form= PasswordChangeForm(user=request.user,data=request.POST)
        if form.is_valid():
            user=form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please enter a correct password.')
    else:
        form= PasswordChangeForm(user=request.user)
    context= {
        'form': form,
        'user': request.user
    }
    return render(request, 'password_change.html', context)
@staff_member_required
def admin_add_game(request):
    if request.method == 'POST':
        form= GameAddForm(request.POST,request.FILES)
        if form.is_valid():
            game=form.save(commit=False)
            messages.success(request, f'Your game {game.title} has been added!')
            game.save()
            return redirect('admin')
        else:
            messages.error(request, 'Please enter a correct game title.')
    else:
        form= GameAddForm(initial={'is_active': True})
    games = Game.objects.all().order_by('-id')
    context= {
        'form': form,
        'user': 'Добавить игру на главную',
        'games': games
    }
    return render(request, 'admin.html',context)

@staff_member_required
def admin_delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if request.method == 'POST':
        title = game.title
        game.delete()
        messages.success(request, f'Игра "{title}" удалена с главной страницы')
        return redirect('admin')

    return redirect('admin')
@login_required
def add_to_cart(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    cart_item, created= CartGame.objects.get_or_create(game=game,user=request.user,defaults={'quantity':1})
    messages.success(request,f"{game.title} добавлена в корзину")
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request,f"{game.title} добавлена в корзину")
    return redirect('cart')

@login_required
def cart_view(request):
    items = CartGame.objects.filter(user=request.user)
    total = sum(item.total_price for item in items)

    return render(request, 'cart.html', {
            'cart_items': items,
            'total': total
    })
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__game')
    return render(request, 'order_history.html', {'orders': orders})


@login_required
def checkout(request):
    cart_items = CartGame.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.warning(request, "Ваша корзина пуста")
        return redirect('cart')

    order = Order.objects.create(
        user=request.user,
        status='pending',
        total_amount=0
    )

    total = 0

    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            game=cart_item.game,
            price_at_purchase=cart_item.game.price,
            quantity=cart_item.quantity
        )
        total += cart_item.total_price

    order.total_amount = total
    order.save()


    cart_items.delete()

    messages.success(request, f"Заказ #{order.id} успешно оформлен на сумму {total} ₽")
    return redirect('order_history')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartGame, id=item_id, user=request.user)

    game_title = cart_item.game.title
    cart_item.delete()

    messages.success(request, f'«{game_title}» удалён из корзины')
    return redirect('cart')
@login_required
def delete_history(request,order_id):
    if request.method == 'POST':
        order=get_object_or_404(Order, id=order_id)
        order.delete()
        return redirect('order_history')
    return redirect('order_history')

#API

@csrf_exempt
@require_http_methods(["GET"])
def api_games_list(request):
    # для получения списка игр
    games = Game.objects.filter(is_active=True).order_by('-created_at')[:50]
    games_data = []

    for game in games:
        games_data.append({
            'id': game.id,
            'title': game.title,
            'description': game.description,
            'price': float(game.price) if game.price else 0.0,
            'image_url': request.build_absolute_uri(game.image.url) if game.image else None,
            'created_at': game.created_at.isoformat() if game.created_at else None,
            'is_active': game.is_active
        })

    return JsonResponse({
        'status': 'success',
        'count': len(games_data),
        'games': games_data
    }, safe=False)


@csrf_exempt
@require_http_methods(["GET"])
def api_game_detail(request, game_id):

    try:
        game = Game.objects.get(id=game_id, is_active=True)
        game_data = {
            'id': game.id,
            'title': game.title,
            'description': game.description,
            'price': float(game.price) if game.price else 0.0,
            'image_url': request.build_absolute_uri(game.image.url) if game.image else None,
            'created_at': game.created_at.isoformat() if game.created_at else None,
            'is_active': game.is_active
        }
        return JsonResponse({'status': 'success', 'game': game_data})
    except Game.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Game not found'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def api_register(request):
    # для регистрации пользователя
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request body raw: {request.body}")
    print(f"DEBUG: Request content type: {request.content_type}")


    try:

        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
                print(f"DEBUG: Parsed data: {data}")
            except UnicodeDecodeError as e:
                print(f"DEBUG: Unicode decode error: {e}")
                try:
                    data = json.loads(request.body.decode('latin-1'))
                    print(f"DEBUG: Parsed with latin-1: {data}")
                except Exception as e2:
                    print(f"DEBUG: Latin-1 decode also failed: {e2}")
                    return JsonResponse({'status': 'error', 'message': 'Encoding error'}, status=400)
        else:
            print("DEBUG: Empty request body")
            return JsonResponse({'status': 'error', 'message': 'Empty request body'}, status=400)

        data = json.loads(request.body.decode('utf-8'))

        # Получаем данные из запроса
        email = data.get('email')
        password1 = data.get('password1')
        password2 = data.get('password2')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        # Проверяем обязательные поля
        if not email or not password1 or not password2:
            return JsonResponse({
                'status': 'error',
                'message': 'Email, password1 and password2 are required'
            }, status=400)

        # Проверяем совпадение паролей
        if password1 != password2:
            return JsonResponse({
                'status': 'error',
                'message': 'Passwords do not match'
            }, status=400)

        # Проверяем минимальную длину пароля
        if len(password1) < 6:
            return JsonResponse({
                'status': 'error',
                'message': 'Password must be at least 6 characters'
            }, status=400)

        # Проверяем валидность email
        if '@' not in email:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid email address'
            }, status=400)

        # Создаем пользователя
        try:
            User = get_user_model()
            # Используем email как username
            user = User.objects.create_user(
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )


            login(request, user)

            return JsonResponse({
                'status': 'success',
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'date_joined': user.date_joined.isoformat() if user.date_joined else None
                }
            }, status=201)  # 201 Created

        except IntegrityError:
            return JsonResponse({
                'status': 'error',
                'message': 'User with this email already exists'
            }, status=409)  # 409 Conflict

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
    except UnicodeDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid encoding'}, status=400)
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Это выведет полную ошибку в консоль сервера
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    # аутентификации пользователя
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def api_user_profile(request):
    """API endpoint для получения профиля пользователя"""
    user = request.user
    return JsonResponse({
        'status': 'success',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_add_to_cart(request):
    """API endpoint для добавления игры в корзину"""
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        quantity = data.get('quantity', 1)

        game = get_object_or_404(Game, id=game_id, is_active=True)
        cart_item, created = CartGame.objects.get_or_create(
            game=game,
            user=request.user,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return JsonResponse({
            'status': 'success',
            'message': f'{game.title} added to cart',
            'cart_item': {
                'id': cart_item.id,
                'game_title': game.title,
                'quantity': cart_item.quantity,
                'total_price': float(cart_item.total_price)
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def api_cart_items(request):
    """API endpoint для получения содержимого корзины"""
    items = CartGame.objects.filter(user=request.user)
    cart_data = []
    total = 0

    for item in items:
        cart_data.append({
            'id': item.id,
            'game_id': item.game.id,
            'game_title': item.game.title,
            'price': float(item.game.price) if item.game.price else 0.0,
            'quantity': item.quantity,
            'total_price': float(item.total_price)
        })
        total += item.total_price

    return JsonResponse({
        'status': 'success',
        'cart_items': cart_data,
        'total': float(total),
        'item_count': len(cart_data)
    }, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_checkout(request):
    """API endpoint для оформления заказа"""
    cart_items = CartGame.objects.filter(user=request.user)

    if not cart_items.exists():
        return JsonResponse({'status': 'error', 'message': 'Cart is empty'}, status=400)

    order = Order.objects.create(
        user=request.user,
        status='pending',
        total_amount=0
    )

    total = 0
    order_items = []

    for cart_item in cart_items:
        order_item = OrderItem.objects.create(
            order=order,
            game=cart_item.game,
            price_at_purchase=cart_item.game.price,
            quantity=cart_item.quantity
        )
        order_items.append({
            'game_title': cart_item.game.title,
            'quantity': cart_item.quantity,
            'price': float(cart_item.game.price)
        })
        total += cart_item.total_price

    order.total_amount = total
    order.save()

    cart_items.delete()

    return JsonResponse({
        'status': 'success',
        'message': 'Order created successfully',
        'order': {
            'id': order.id,
            'status': order.status,
            'total_amount': float(total),
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'items': order_items
        }
    })


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def api_order_history(request):
    """API endpoint для получения истории заказов"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__game')
    orders_data = []

    for order in orders:
        items_data = []
        for item in order.items.all():
            items_data.append({
                'game_title': item.game.title,
                'quantity': item.quantity,
                'price_at_purchase': float(item.price_at_purchase),
                'total': float(item.price_at_purchase * item.quantity)
            })

        orders_data.append({
            'id': order.id,
            'status': order.status,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'items': items_data
        })

    return JsonResponse({
        'status': 'success',
        'orders': orders_data,
        'order_count': len(orders_data)
    }, safe=False)


class CatalogViews(TemplateView):
    template_name = 'catalog.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games']=Game.objects.filter(is_active=True).order_by('-created_at')[:12]
        return context
