from audioop import reverse
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm, UserModel
from django.contrib.auth import authenticate, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import modelformset_factory
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from rest_framework import generics
from .forms import SearchForm, RegisterForm, ProductForm, ImageForm, OrderForm, ReviewForm
from .models import Image, ProductSerializer, Cart
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.views import View
from .models import CartItem, Product
from django.http import JsonResponse


#Рендерит сам сайт
def index(request):
    return render(request, "base.html")


#Эта функция поиска он работает, при вводе названия продукта и он показывает его характеристики
def sdu_search(request):
    search_text = request.GET.get("search", "")
    form = SearchForm(request.GET)
    products = Product.objects.filter(product_name__icontains=search_text)
    return render(request, "search-result.html", {"form": form, "search_text": search_text, "products": products})


#Это фукция отображает список продуктов ламода потому-что у меня была ламода раньше хаха
def sdu_detail(request):
    products = Product.objects.filter(status='published')
    context = {'products': products}
    return render(request, 'lamoda_detail.html', context)


#Эта функция отвечает за детали его там фото и характеристика каждого продукта и можно оставлять
# отзывы если юзер за логинился а если нет то она не работает и также тут показывает на какие последние продукты заходил юзер
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Get last viewed items from session
    last_viewed = request.session.get('last_viewed', [])

    # Check if the current product is already in the last viewed items list
    if pk in last_viewed:
        last_viewed.remove(pk)

    # Add the current product to the last viewed items list
    last_viewed.insert(0, pk)

    # Keep only the last 5 viewed items
    last_viewed = last_viewed[:5]

    # Save the updated last viewed items list to the session
    request.session['last_viewed'] = last_viewed

    # Get the actual product objects for the last viewed items
    last_viewed_products = Product.objects.filter(pk__in=last_viewed)

    # Handle review form submission
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been submitted.')
            return redirect('product_detail', pk=pk)
    else:
        form = ReviewForm()

    return render(request, 'product_detail.html', {
        'product': product,
        'last_viewed_products': last_viewed_products,
        'form': form,
    })

#способствует добавление продуктов в баскет
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product)
    return redirect('cart_detail')


#также способствует добавлеение предметов в баскет
@login_required
def add_to_cart(request, product_id):
    user = request.user
    product = get_object_or_404(Product, pk=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return JsonResponse({'success': True})


#Удаляет продукты из корзины
def remove_from_cart(request, product_id):
    try:
        item = CartItem.objects.get(user=request.user, product__id=product_id)
        item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('basket')


#Сама корзина в ней хранятся продукты после добавление в разделе продукты
@login_required
def basket(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = CartItem.objects.filter(user=request.user)
    cart_total = sum(item.product.price * item.quantity for item in cart_items)

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
    }

    return render(request, 'basket.html', context=context)


#после просмотра продукта юзер нажимает на кнопку checkout и перебрасывает его на checkout
@login_required
def checkout(request):
    if request.method == 'POST':
        # Обработка заказа
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']

        # Отправка письма
        subject = 'Order confirmation'
        message = f'Thanks for the order, {name}! Your order has been successfully placed. We will contact you by number{phone} or by email {email},when your order is ready to ship.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list)

        # Очистка корзины
        request.user.cartitem_set.all().delete()

        return render(request, 'order_information_email.html')

    else:
        form = OrderForm()

    return render(request, 'checkout.html', {'form': form})


#тут идет регистрация аккаунта
class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.pk) + str(timestamp) +
                str(user.is_active)
        )


account_activation_token = AccountActivationTokenGenerator()


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegisterForm
    template_name = 'register.html'
    success_url = reverse_lazy('base')
    success_message = 'Please check your email to activate your account'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        current_site = get_current_site(self.request)
        subject = 'Confirm your registration'
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_url = reverse_lazy('activate_view', kwargs={'uidb64': uidb64, 'token': token})
        confirmation_url = f'http://{current_site.domain}{activation_url}'
        message = render_to_string('email_verification.html', {
            'user': user,
            'domain': current_site.domain,
            'confirmation_url': confirmation_url,
        })
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        return super().form_valid(form)


User = get_user_model()


#Активация аккаунта
def activate_view(request, uidb64, token):
    try:
        uid = str(urlsafe_base64_decode(uidb64), 'utf-8')
        user = User.objects.get(pk=uid)
        if not user.is_active:
            user.is_active = True
            user.save()
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully!')
        return redirect(reverse('login'))
    else:
        messages.error(request, 'Activation link is invalid or has expired! or already activated')
        return render(request, 'activation.html')


#Вхождение в аккаунт
class LoginView(View):
    template_name = 'login.html'
    form_class = AuthenticationForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Check for empty fields
            if not username or not password:
                messages.error(request, 'Username and password are required')
                return redirect('login')

            user = authenticate(request, username=username, password=password)

            # Check for invalid login
            if user is None:
                messages.error(request, 'Invalid username or password')
                return redirect('login')

            login(request, user)
            messages.success(request, 'You have successfully logged in')
            return redirect('base')

        return render(request, self.template_name, {'form': form})


#Выход из аккаунта
@login_required
def logout_view(request):
    logout(request)
    return redirect('base')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = get_object_or_404(User, email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_password_link = request.build_absolute_uri('/') + f'reset-password/{uid}/{token}/'

        send_mail(
            'Password Recovery',
            f'Link to password recovery: {reset_password_link}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        messages.success(request, 'A link to password recovery was sent to ваш email')
        return redirect('login')
    else:
        return render(request, 'forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            user.set_password(password)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been successfully changed. Now you can log in.')
            return redirect('login')
        else:
            return render(request, 'reset_password.html')
    else:
        messages.error(request, 'The password recovery link is invalid.')
        return redirect('login')


#Функция добавления продукта
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class AddProductView(View):
    template_name = 'add_product.html'
    product_form_class = ProductForm
    image_formset_class = modelformset_factory(Image, form=ImageForm, extra=1)

    @method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Create empty product and image formsets for display
        product_form = self.product_form_class()
        image_formset = self.image_formset_class()
        context = {'product_form': product_form, 'image_formset': image_formset}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Create product and image formsets
        product_form = self.product_form_class(request.POST)
        image_formset = self.image_formset_class(request.POST, request.FILES)

        # If forms are valid, save data and redirect to product list page
        if product_form.is_valid() and image_formset.is_valid():
            product = product_form.save(commit=False)  # Don't save the product yet
            product.is_published = False  # Set is_published to False
            product.save()  # Save the product
            instances = image_formset.save(commit=False)
            for instance in instances:
                instance.product = product
                instance.save()
            return redirect(reverse('product_list'))

        # If forms are not valid, render the page with the forms and errors
        context = {'product_form': product_form, 'image_formset': image_formset}
        return render(request, self.template_name, context)


#Удаление продукта
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class DeleteProductView(View):
    template_name = 'delete_product.html'

    def get(self, request, *args, **kwargs):
        products = Product.objects.all()
        context = {'products': products}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return redirect('product_list')


#Обновление продукта
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class UpdateProductView(View):
    template_name = 'update_product.html'

    def get(self, request, *args, **kwargs):
        form = ProductForm()
        products = Product.objects.all()
        context = {'form': form, 'products': products}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')

        products = Product.objects.all()
        context = {'form': form, 'products': products}
        return render(request, self.template_name, context)


#Просмотр пользователя
class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

#Эти коды по логике должны работать так когда юзер заходит на edit-profile н не может себя делать staff
def is_admin(user):
    return user.is_superuser


@user_passes_test(lambda u: u.is_superuser)
def make_staff(request, pk):
    user = User.objects.get(pk=pk)
    if request.user.groups.filter(name='superuser').exists():  # Проверка на принадлежность к группе
        user.is_staff = True
        user.save()
        messages.success(request, f'{user.username} is now a staff member')
        return redirect('user_profile')
    else:
        messages.error(request, 'You are not authorized to perform this action')
        return redirect('user_profile')


class EditUserProfileView(LoginRequiredMixin, FormView):
    form_class = UserChangeForm
    template_name = 'edit_profile.html'
    success_url = reverse_lazy('user_profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)
        if self.request.user.is_superuser or self.request.user == user:
            if not self.request.user.is_superuser and form.cleaned_data.get('is_staff'):
                messages.error(self.request, 'You are not authorized to make yourself a staff member')
                return self.form_invalid(form)
            user.save()
            messages.success(self.request, 'Profile updated successfully')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'You are not authorized to edit this profile')
            return self.form_invalid(form)


class CreateUserView(LoginRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'create_user.html'
    success_url = reverse_lazy('user_list')


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class UserEditView(View):
    form_class = UserChangeForm
    template_name = 'edit_user.html'

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        form = self.form_class(instance=user)
        return render(request, self.template_name, {'form': form, 'user': user})

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        form = self.form_class(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'The user profile has been successfully updated.')
            return redirect('user_list')
        return render(request, self.template_name, {'form': form, 'user': user})


# Delete User View
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class UserDeleteView(DeleteView):
    model = User
    template_name = 'delete_user.html'
    success_url = reverse_lazy('user_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'The user has been successfully deleted.')
        return super().delete(request, *args, **kwargs)


class UserListView(LoginRequiredMixin, TemplateView):
    template_name = 'user_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context


@user_passes_test(lambda u: u.is_superuser)
def pending_products(request):
    pending_products = Product.objects.filter(is_published=False)

    if request.method == 'POST':
        for product_id in request.POST.getlist('products'):
            product = get_object_or_404(Product, pk=product_id)
            if 'publish' in request.POST:
                product.is_published = True
                product.save()
            elif 'reject' in request.POST:
                product.delete()

    if request.user.is_superuser:
        return render(request, 'pending_products.html', {'pending_products': pending_products})
    else:
        return render(request, 'error.html', {'message': 'You do not have permission to view this page.'})


#Это API проекта
class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
