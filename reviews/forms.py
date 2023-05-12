
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Product, Image, Review
from django import forms
from django.core.exceptions import ValidationError


#Форма найти продукт
class SearchForm(forms.Form):
    search = forms.CharField(required=False, min_length=3)
    search_in = forms.ChoiceField(required=False,choices=(("category", "Category"),("brand", "Brand")))


#Авторизация
class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': (
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': ("This account is inactive."),
    }

    #Подтверждение акка
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not any(char.isupper() for char in password1):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password1):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")
        if not any(char.isdigit() for char in password1):
            raise forms.ValidationError("Password must contain at least one number.")
        return password1


class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'description', 'price', 'category', 'brand', 'color', 'size', 'weight', 'material', 'rating']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CustomUserCreationForm(UserCreationForm):
    is_active = forms.BooleanField(label='Is active', required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'is_active',)


class ImageAdminForm(forms.ModelForm):
    image = forms.ImageField(widget=AdminFileWidget)

    class Meta:
        model = Image
        fields = '__all__'


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        if image:
            # Проверяем расширение файла
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError('This file format is not supported.')

            # Проверяем размер файла
            max_size = 5 * 1024 * 1024  # 5 MB
            if image.size > max_size:
                raise ValidationError('File size cannot exceed 5 MB.')


class OrderForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    address = forms.CharField(max_length=250)
    payment_method = forms.ChoiceField(choices=(('master_card', 'Master Card'), ('paypal', 'PayPal')))


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write your review here...'}),
        }