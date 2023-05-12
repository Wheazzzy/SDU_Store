"""
URL configuration for lamoda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from reviews.views import sdu_detail
import reviews.views
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from reviews.views import AddProductView
from django.contrib.auth.decorators import login_required
from reviews.views import DeleteProductView
from reviews.views import UpdateProductView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', reviews.views.index, name='base'),
    path('sdu-search/', reviews.views.sdu_search, name='sdu_search'),
    path('products/', reviews.views.sdu_detail, name='product_list'),
    path('add_product/', AddProductView.as_view(), name='add_product'),
    path('register/', reviews.views.RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(template_name='login.html', success_url='base'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('delete_product/', DeleteProductView.as_view(), name='delete_product'),
    path('update_product/', UpdateProductView.as_view(), name='update_product'),
    path('activate/<str:uidb64>/<str:token>/', reviews.views.activate_view, name='activate_view'),
    path('profile/', login_required(reviews.views.UserProfileView.as_view()), name='user_profile'),
    path('profile/edit/', login_required(reviews.views.EditUserProfileView.as_view()), name='edit_user_profile'),
    path('users/create/', reviews.views.CreateUserView.as_view(), name='create_user'),
    path('users/edit/<int:user_id>/', reviews.views.UserEditView.as_view(), name='edit_user'),
    path('users/delete/<int:pk>/', reviews.views.UserDeleteView.as_view(), name='delete_user'),
    path('users/', reviews.views.UserListView.as_view(), name='user_list'),
    path('pending_products/', reviews.views.pending_products, name='pending_products'),
    path('product/<int:pk>/', reviews.views.product_detail, name='product_detail'),
    path('products_api/', reviews.views.ProductList.as_view()),
    path('add-to-cart/<int:product_id>/', reviews.views.add_to_cart, name='add-to-cart'),
    path('basket/', reviews.views.basket, name='basket'),
    path('checkout/', reviews.views.checkout, name='checkout'),
    path('remove-from-cart/<int:product_id>/', reviews.views.remove_from_cart, name='remove_from_cart'),
    path('order-confirmation/', reviews.views.checkout, name='order_confirmation'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

