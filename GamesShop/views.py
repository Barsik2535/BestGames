import profile
from urllib import request

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView, TemplateView
from django.contrib.auth import update_session_auth_hash
from GamesShop.forms import CustomUserCreationForm, LoginForm, ProfileEditForm, PasswordChangeForm, GameAddForm
from GamesShop.models import Game, CartGame, Order, OrderItem


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
            print("DEBUG LOGIN ATTEMPT:")
            print(f"  Email: '{email}'")
            print(f"  Password: {password[:3]}***")
            user = authenticate(username=email, password=password)
            print(f"  Authenticate result: {user}")
            if user is not None:
                print('SUCCESS')
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