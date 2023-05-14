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


# Рендерит сам сайт
def index(request):
    return render(request, "base.html")


# Эта функция поиска он работает, при вводе названия продукта и он показывает его характеристики
def sdu_search(request):  # это объявление функции "sdu_search", которая принимает запрос "request".
    search_text = request.GET.get("search",
                                  "")  # это получение значения параметра "search" из запроса, который пользователь вводит в форме поиска. Если параметр не существует, значение по умолчанию устанавливается на пустую строку.
    form = SearchForm(request.GET)  # это инициализация формы поиска с переданным в запросе значением "search".
    products = Product.objects.filter(
        product_name__icontains=search_text)  # это выполнение фильтрации продуктов в базе данных по названию продукта, используя "icontains" для выполнения поиска по подстроке. Результаты сохраняются в переменной "products".
    return render(request, "search-result.html", {"form": form, "search_text": search_text, "products": products})


# Это фукция отображает список продуктов ламода потому-что у меня была ламода раньше хаха
def sdu_detail(request):
    products = Product.objects.filter(status='published')
    context = {'products': products}
    return render(request, 'lamoda_detail.html', context)


# Эта функция отвечает за детали его там фото и характеристика каждого продукта и можно оставлять
# отзывы если юзер за логинился а если нет то она не работает и также тут показывает на какие последние продукты заходил юзер
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)  # Получение объекта продукта с заданным id:

    # Получаем список последних просмотренных товаров из сессии
    last_viewed = request.session.get('last_viewed', [])

    # Проверяем, если текущий товар уже есть в списке последних просмотренных товаров
    if pk in last_viewed:
        last_viewed.remove(pk)

    # Добавляем текущий товар в начало списка последних просмотренных товаров
    last_viewed.insert(0, pk)

    # Оставляем в списке только последние 5 просмотренных товаров
    last_viewed = last_viewed[:5]

    # Сохраняем обновленный список последних просмотренных товаров в сессии
    request.session['last_viewed'] = last_viewed

    # Получаем объекты последних просмотренных товаров из базы данных
    last_viewed_products = Product.objects.filter(pk__in=last_viewed)

    # Если форма отправлена методом POST
    if request.method == 'POST':  # Создаем объект формы, передав ему данные, полученные из POST запроса
        form = ReviewForm(request.POST)
        if form.is_valid():  # Проверяем, что данные формы валидны
            review = form.save(commit=False)  # Создаем объект отзыва, но не сохраняем его в базе данных
            review.product = product  # Устанавливаем связь с текущим товаром и текущим пользователем
            review.user = request.user
            review.save()  # Сохраняем объект отзыва в базе данных
            messages.success(request,
                             'Your review has been submitted.')  # Показываем сообщение об успешной отправке отзыва
            return redirect('product_detail', pk=pk)  # Перенаправляем пользователя на страницу текущего товара
    # Если форма не отправлена, создаем пустую форму
    else:
        form = ReviewForm()
    # Отображение страницы с детальной информацией о товаре:
    return render(request, 'product_detail.html', {
        'product': product,
        'last_viewed_products': last_viewed_products,
        'form': form,
    })


# способствует добавление продуктов в баскет
# Затем метод add() объекта cart добавляет выбранный продукт в корзину.
# В конце функция перенаправляет пользователя на страницу корзины (cart_detail).
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product)
    return redirect('cart_detail')


# также способствует добавлеение предметов в баскет
# сли пользователь уже добавил продукт, то функция увеличивает количество этого продукта в корзине на 1.
# Если продукт не был добавлен ранее, функция создает новый объект CartItem и устанавливает его количество в 1.
# Затем функция возвращает JSON-ответ со статусом успеха.
@login_required
def add_to_cart(request, product_id):
    user = request.user
    product = get_object_or_404(Product, pk=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return JsonResponse({'success': True})


# Удаляет продукты из корзины
# получает product_id из запроса и ищет объект CartItem, который относится к текущему пользователю и имеет product_id.
# Если такой объект существует, он удаляется.
# Если объект не найден, функция ничего не делает.
# Затем функция перенаправляет пользователя на страницу корзины.
def remove_from_cart(request, product_id):
    try:
        item = CartItem.objects.get(user=request.user, product__id=product_id)
        item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('basket')


# Сама корзина в ней хранятся продукты после добавление в разделе продукты
# Представление извлекает корзину покупок пользователя (объект Cart) и связанные с ней объекты CartItem, используя filter() для запроса к базе данных.
# Затем он вычисляет общую стоимость всех товаров в корзине, умножая цену каждого товара в корзине на его количество и
# суммируя результаты с помощью встроенной в Python функции sum().
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


# после просмотра продукта юзер нажимает на кнопку checkout и перебрасывает его на checkout
# Первые 4 строки отвечают за обработку POST-запроса, который отправляется при подтверждении заказа.
# Если это POST-запрос, то извлекаются данные из формы, которую пользователь заполняет на странице оформления заказа (имя, email и телефон).
# Затем происходит отправка email-сообщения пользователю, который сделал заказ. Это происходит при помощи функции send_mail из библиотеки Django.
# Далее, если заказ успешно отправлен, корзина пользователя очищается - удаляются все товары, которые находятся в корзине.
# Если же это GET-запрос, т.е. пользователь только переходит на страницу оформления заказа, то ему отображается форма для заполнения информации о заказе.
# В итоге функция возвращает страницу оформления заказа, на которой расположена форма для заполнения информации о заказе.
# Если заказ был успешно отправлен, то возвращается страница с информацией о заказе.
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


# тут идет регистрация аккаунта
# Код регистрации аккаунта отвечает за создание нового пользователя и отправку электронного письма для активации учетной записи.
# Здесь определен класс AccountActivationTokenGenerator, который наследуется от класса PasswordResetTokenGenerator.
# Этот класс определяет, как должен быть создан токен для активации учетной записи.

# Затем определен класс RegisterView, который наследуется от класса CreateView. Этот класс определяет, как должен работать процесс
# регистрации нового пользователя. Он использует форму RegisterForm для создания нового пользователя, проверяет, что электронная почта
# не была зарегистрирована ранее, создает нового пользователя, но не активирует его учетную запись, отправляет электронное
# письмо с ссылкой для активации учетной записи и выводит сообщение об успешной регистрации. Когда пользователь активирует
# свою учетную запись, он может войти в систему и использовать все ее функции.
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
        email = form.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            form.add_error('email', 'This email is already registered')
            return super().form_invalid(form)

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


# код относится к функции, которая активирует аккаунт пользователя. Функция принимает запрос, уникальный идентификатор пользователя
# (представленный в виде строки, полученной из декодированного urlsafe_base64-кодированного значения) и токен, который был
# создан для пользователя. Функция пытается извлечь пользователя из базы данных с помощью переданного идентификатора, затем
# проверяет токен с помощью стандартного токен-генератора Django. Если пользователь найден и токен действителен, то его аккаунт
# будет активирован и он будет перенаправлен на страницу входа в систему. В противном случае пользователь будет уведомлен о том,
# что ссылка для активации недействительна или устарела.
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


# Вхождение в аккаунт
# представление для входа в систему. Здесь используется класс LoginView, который является наследником базового класса View.
# Класс имеет два метода: get и post.
# Метод get вызывается, когда пользователь обращается к этой странице в первый раз. Он возвращает страницу с формой входа,
# созданной с помощью класса AuthenticationForm.
# Метод post вызывается, когда пользователь отправляет форму на странице входа. Метод проверяет, валидна ли форма, и если да,
# то пытается аутентифицировать пользователя с помощью authenticate(). Если пользователь успешно аутентифицирован,
# то он авторизуется с помощью функции login(), после чего пользователь перенаправляется на главную страницу.
# Если пользователь не аутентифицирован или форма невалидна, то пользователь перенаправляется на страницу входа,
# где показываются соответствующие сообщения об ошибке с помощью модуля messages.
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


# Выход из аккаунта
@login_required
def logout_view(request):
    logout(request)
    return redirect('base')


def forgot_password(request):
    if request.method == 'POST':  # Определяем функцию forgot_password с одним параметром request, который представляет запрос, полученный от клиента.
        email = request.POST.get('email')  # Проверяем, был ли запрос отправлен методом POST.
        user = get_object_or_404(User,
                                 email=email)  # Извлекаем адрес электронной почты, который был введен в форму на странице forgot_password.html.
        token = default_token_generator.make_token(
            user)  # Получаем объект пользователя с помощью адреса электронной почты. Если пользователь не найден, возвращается страница 404.
        uid = urlsafe_base64_encode(
            force_bytes(user.pk))  # Генерируем токен сброса пароля с помощью объекта default_token_generator.
        reset_password_link = request.build_absolute_uri(
            '/') + f'reset-password/{uid}/{token}/'  # Кодируем идентификатор пользователя в строку base64 с помощью функций force_bytes и urlsafe_base64_encode.
        # Формируем ссылку для сброса пароля, которая будет отправлена по электронной почте пользователю. Эта ссылка содержит идентификатор пользователя и токен сброса пароля.
        send_mail(
            'Password Recovery',
            f'Link to password recovery: {reset_password_link}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        # Отправляем письмо на адрес электронной почты пользователя с ссылкой для сброса пароля.
        messages.success(request, 'A link to password recovery was sent to ваш email')
        return redirect('login')
    else:
        return render(request, 'forgot_password.html')


def reset_password(request, uidb64, token):
    # декодируем идентификатор пользователя из строки base64 и получаем соответствующего пользователя
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # проверяем, что пользователь существует и токен для восстановления пароля действителен
    if user is not None and default_token_generator.check_token(user, token):
        # если запрос методом POST, то обрабатываем форму с новым паролем
        if request.method == 'POST':
            # получаем новый пароль из формы
            password = request.POST.get('password')
            # устанавливаем новый пароль для пользователя и сохраняем его
            user.set_password(password)
            user.save()
            # обновляем сессию аутентификации пользователя
            update_session_auth_hash(request, user)
            # отправляем пользователю сообщение об успешном изменении пароля и перенаправляем на страницу входа
            messages.success(request, 'Your password has been successfully changed. Now you can log in.')
            return redirect('login')
        else:
            # если запрос методом GET, то просто отображаем форму для ввода нового пароля
            return render(request, 'reset_password.html')
    else:
        # если пользователь или токен не действительны, то отправляем сообщение об ошибке и перенаправляем на страницу входа
        messages.error(request, 'The password recovery link is invalid.')
        return redirect('login')


# Функция добавления продукта
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class AddProductView(View):
    template_name = 'add_product.html'
    product_form_class = ProductForm
    image_formset_class = modelformset_factory(Image, form=ImageForm, extra=1)

    # Переопределение метода dispatch с использованием декоратора, который проверяет, является ли пользователь суперпользователем
    @method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # Обработка GET-запроса
    def get(self, request, *args, **kwargs):
        # Создание пустых форм для продукта и изображений
        product_form = self.product_form_class()
        image_formset = self.image_formset_class()
        context = {'product_form': product_form, 'image_formset': image_formset}
        # Отображение страницы с формами
        return render(request, self.template_name, context)

    # Обработка POST-запроса
    def post(self, request, *args, **kwargs):
        # Создание форм для продукта и изображений
        product_form = self.product_form_class(request.POST)
        image_formset = self.image_formset_class(request.POST, request.FILES)

        # Если формы валидны, сохраняем данные и перенаправляем на страницу списка продуктов
        if product_form.is_valid() and image_formset.is_valid():
            product = product_form.save(commit=False)  # Не сохраняем продукт пока
            product.is_published = False  # Устанавливаем is_published на False
            product.save()  # Сохраняем продукт
            instances = image_formset.save(commit=False)
            for instance in instances:
                instance.product = product
                instance.save()
            return redirect(reverse('product_list'))

        # Если формы не валидны, отображаем страницу с формами и ошибками
        context = {'product_form': product_form, 'image_formset': image_formset}
        return render(request, self.template_name, context)


# Удаление продукта
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class DeleteProductView(View):
    template_name = 'delete_product.html'

    def get(self, request, *args, **kwargs):
        # Получаем все объекты продуктов
        products = Product.objects.all()
        context = {'products': products}
        # Рендерим страницу с продуктами для удаления
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Получаем id удаляемого продукта из POST запроса
        product_id = request.POST.get('product_id')
        # Получаем объект продукта по id или 404 если объект не найден
        product = get_object_or_404(Product, id=product_id)
        # Удаляем продукт
        product.delete()
        # Редирект на страницу со списком продуктов
        return redirect('product_list')


# Конструкция "@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')"
# применяется для проверки доступа к представлению, и обертывает класс "UpdateProductView".
# Она гарантирует, что только пользователи, которые являются суперпользователями (имеют атрибут is_superuser равный True),
# имеют доступ к данному представлению.
# Класс "UpdateProductView" наследует класс "View". Он отображает форму для редактирования существующего продукта.
# В атрибуте "template_name" хранится имя шаблона, который будет использоваться для отображения формы редактирования продукта.
# В методе "get" создается экземпляр формы для продукта и выбираются все продукты из базы данных.
# Затем данные формы и список продуктов передаются в шаблон для их отображения.
# Метод "post" обрабатывает отправленную пользователем форму. Из POST-запроса извлекается ID редактируемого продукта,
# и затем из базы данных извлекается экземпляр продукта с этим ID. Создается экземпляр формы для этого продукта,
# заполненный переданными в POST-запросе данными. Если форма проходит валидацию, данные сохраняются в
# базу данных и происходит перенаправление на страницу списка продуктов.
# Если форма не проходит валидацию, она возвращается на страницу редактирования продукта,
# где отображается сообщение об ошибках и введенные пользователем данные.
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


# Просмотр пользователя
class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


# Эти коды по логике должны работать так когда юзер заходит на edit-profile н не может себя делать staff
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
    # Используем форму UserChangeForm для редактирования профиля пользователя
    form_class = UserChangeForm
    # Указываем шаблон, который будет использоваться для отображения страницы редактирования профиля пользователя
    template_name = 'edit_profile.html'
    # Указываем URL, на который будет перенаправлен пользователь после успешного сохранения профиля
    success_url = reverse_lazy('user_profile')

    def get_form_kwargs(self):
        # Получаем аргументы для создания формы
        kwargs = super().get_form_kwargs()
        # Устанавливаем instance (экземпляр) формы в качестве текущего пользователя
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Получаем пользовательские данные из формы
        user = form.save(commit=False)
        # Проверяем, является ли текущий пользователь суперпользователем или пользователем, чей профиль редактируется
        if self.request.user.is_superuser or self.request.user == user:
            # Проверяем, что текущий пользователь является суперпользователем или что не пытается сделать самого себя сотрудником
            if not self.request.user.is_superuser and form.cleaned_data.get('is_staff'):
                # Если текущий пользователь не является суперпользователем и пытается сделать самого себя сотрудником, выводим сообщение об ошибке
                messages.error(self.request, 'You are not authorized to make yourself a staff member')
                # Возвращаем форму с невалидными данными, чтобы пользователь мог исправить ошибки
                return self.form_invalid(form)
            # Сохраняем профиль пользователя
            user.save()
            # Выводим сообщение об успешном сохранении профиля
            messages.success(self.request, 'Profile updated successfully')
            # Перенаправляем пользователя на страницу с его профилем
            return super().form_valid(form)
        else:
            # Если текущий пользователь не является суперпользователем и не редактирует свой собственный профиль, выводим сообщение об ошибке
            messages.error(self.request, 'You are not authorized to edit this profile')
            # Возвращаем форму с невалидными данными, чтобы пользователь мог исправить ошибки
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

    # GET-запрос для получения формы редактирования пользователя
    def get(self, request, user_id):
        # Получаем пользователя по его идентификатору или возвращаем 404-ошибку, если пользователь не найден
        user = get_object_or_404(User, id=user_id)
        # Создаем экземпляр формы с заполненными данными пользователя
        form = self.form_class(instance=user)
        # Рендерим шаблон с формой и информацией о пользователе
        return render(request, self.template_name, {'form': form, 'user': user})

    # POST-запрос для сохранения изменений пользователя
    def post(self, request, user_id):
        # Получаем пользователя по его идентификатору или возвращаем 404-ошибку, если пользователь не найден
        user = get_object_or_404(User, id=user_id)
        # Создаем экземпляр формы с заполненными данными из POST-запроса и существующим пользователем
        form = self.form_class(request.POST, instance=user)
        # Если форма проходит валидацию, сохраняем изменения
        if form.is_valid():
            form.save()
            # Отображаем сообщение об успешном обновлении профиля пользователя и перенаправляем на страницу списка пользователей
            messages.success(request, 'The user profile has been successfully updated.')
            return redirect('user_list')
        # Иначе рендерим шаблон с формой и информацией о пользователе для исправления ошибок
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


# Это API проекта
class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
