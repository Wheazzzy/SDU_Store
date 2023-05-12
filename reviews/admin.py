
from .models import Product
from .forms import CustomUserCreationForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from .models import Image
from .forms import ImageAdminForm
# Register your models here.
# admin.site.register(Product)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    form = ImageAdminForm


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'brand', 'status')
    list_filter = ('category', 'brand', 'status')
    search_fields = ('product_name', 'category__category_name', 'brand__brand_name')

    def save_model(self, request, obj, form, change):
        if not obj.id and obj.status != 'published':
            obj.status = 'draft'
        obj.save()


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)