# Отчет о реализации требований проекта

## Содержание
1. [Регистрация моделей в админке](#1-регистрация-моделей-в-админке)
2. [Параметры on_delete для связей ForeignKey](#2-параметры-on_delete-для-связей-foreignkey)
3. [Редактирование полей is_published и pub_date](#3-редактирование-полей-is_published-и-pub_date)
4. [Содержательные имена параметров URL](#4-содержательные-имена-параметров-url)
5. [Тип параметра username в URL](#5-тип-параметра-username-в-url)
6. [Использование именованных маршрутов](#6-использование-именованных-маршрутов)
7. [Использование get_object_or_404()](#7-использование-get_object_or_404)
8. [Количество комментариев к постам](#8-количество-комментариев-к-постам)
9. [Функция вычисления количества комментариев](#9-функция-вычисления-количества-комментариев)
10. [Сортировка после annotate()](#10-сортировка-после-annotate)
11. [Функция пагинации](#11-функция-пагинации)
12. [Фильтрация постов для автора](#12-фильтрация-постов-для-автора)
13. [Фильтрация по опубликованности](#13-фильтрация-по-опубликованности)
14. [Декоратор @login_required](#14-декоратор-login_required)
15. [Использование redirect() без reverse()](#15-использование-redirect-без-reverse)
16. [Проверка авторства поста](#16-проверка-авторства-поста)

---

## 1. Регистрация моделей в админке

Все модели представлены в админке Django:

```python
# blog/admin.py
from django.contrib import admin
from .models import Category, Location, Post, Comment

class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_published',
        'created_at'
    )
    list_editable = ('is_published',)
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_published',
        'created_at'
    )
    list_editable = ('is_published',)
    list_filter = ('is_published', 'created_at')
    search_fields = ('name',)

class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'author',
        'category',
        'location',
        'is_published',
    )
    list_editable = ('is_published',)
    list_filter = (
        'is_published',
        'category',
        'location',
        'pub_date'
    )
    search_fields = ('title', 'text')
    date_hierarchy = 'pub_date'
    ordering = ('-pub_date',)

class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'author',
        'post',
        'created_at',
    )
    list_filter = ('created_at', 'author', 'post')
    search_fields = ('text',)
    date_hierarchy = 'created_at'

admin.site.register(Post, PostAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Comment, CommentAdmin)
```

**Назначение**: Обеспечивает удобный интерфейс администратора для управления контентом сайта.

---

## 2. Параметры on_delete для связей ForeignKey

Во всех моделях правильно указаны параметры on_delete для связей:

```python
# blog/models.py
class Post(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Удаляем пост при удалении автора
        verbose_name='Автор публикации',
        related_name='posts'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,  # Устанавливаем NULL при удалении локации
        null=True,
        blank=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,  # Устанавливаем NULL при удалении категории
        null=True,
        verbose_name='Категория'
    )
    
class Comment(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Удаляем комментарий при удалении автора
        verbose_name='Автор комментария'
    )
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE,  # Удаляем комментарии при удалении поста
        null=True,
        verbose_name='Публикация',
        related_name='comments'
    )
```

**Назначение**: Обеспечивает целостность данных при удалении связанных записей.

---

## 3. Редактирование полей is_published и pub_date

Форма поста позволяет редактировать эти поля:

```python
# blog/forms.py
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'created_at')  # Не включаем author и created_at
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'datetime-local'}),
            'is_published': forms.CheckboxInput(),
        }
```

**Назначение**: Позволяет автору изменять статус публикации и дату публикации поста.

---

## 4. Содержательные имена параметров URL

URL-параметры имеют содержательные имена:

```python
# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.MainPostView.as_view(), name='index'),
    path('posts/<int:post_id>/', views.PostDetailView.as_view(),
         name='post_detail'),
    path('category/<slug:category_slug>/', views.CategoryPostView.as_view(),
         name='category_posts'),
    path('profile/<str:username>/', views.ProfileView.as_view(),
         name='profile'),
    path('posts/create/', views.CreatePostView.as_view(),
         name='create_post'),
    path('posts/<int:post_id>/edit/', views.PostUpdateView.as_view(),
         name='edit_post'),
    path('posts/<int:post_id>/delete/', views.PostDeleteView.as_view(),
         name='delete_post'),
    path('posts/<int:post_id>/comment/', views.CommentCreateView.as_view(),
         name='add_comment'),
    path('posts/<int:post_id>/edit_comment/<int:comment_id>/',
         views.CommentUpdateView.as_view(), name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<int:comment_id>/',
         views.CommentDeleteView.as_view(), name='delete_comment')
]
```

**Назначение**: Использование содержательных имен параметров улучшает читаемость кода и делает маршруты более понятными.

---

## 5. Тип параметра username в URL

Для имени пользователя используется тип `str`, а не `slug`:

```python
# blog/urls.py
path('profile/<str:username>/', views.ProfileView.as_view(),
     name='profile'),
```

**Назначение**: Тип `str` более подходящий для ников пользователей, чем `slug`, так как позволяет использовать более широкий набор символов.

---

## 6. Использование именованных маршрутов

В проекте используются именованные маршруты:

```python
# blog/views.py
from django.urls import reverse_lazy, reverse

class CreatePostView(LoginRequiredMixin, CreateView):
    # ...
    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user.username
        })

class PostUpdateView(LoginRequiredMixin, UpdateView):
    # ...
    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.id})

# В шаблонах
# templates/includes/post_card.html
<a href="{% url 'blog:post_detail' post.id %}" class="card-link text-muted">Комментарии ({{ post.comment_count }})</a>
```

**Назначение**: Использование именованных маршрутов позволяет избежать дублирования URL и облегчает поддержку кода.

---

## 7. Использование get_object_or_404()

Все извлечения из базы данных выполняются через get_object_or_404():

```python
# blog/views.py
from django.shortcuts import get_object_or_404

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])

        if self.request.user == post.author:
            return post

        return get_object_or_404(
            get_posts_with_filters(apply_filters=True, add_comments=False),
            id=self.kwargs['post_id']
        )

class CommentCreateView(LoginRequiredMixin, CreateView):
    # ...
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        return super().form_valid(form)
```

**Назначение**: Обеспечивает корректную обработку ситуаций, когда запрашиваемый объект не найден, возвращая HTTP 404 ошибку.

---

## 8. Количество комментариев к постам

Посты в наборах дополнены количеством комментариев:

```python
# blog/views.py
from django.db.models import Count

def get_posts_with_filters(posts_queryset=None, apply_filters=True, add_comments=True):
    if posts_queryset is None:
        posts_queryset = Post.objects.all()

    if apply_filters:
        posts_queryset = posts_queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )

    posts_queryset = posts_queryset.select_related(
        'author', 'category', 'location'
    )

    if add_comments:
        posts_queryset = posts_queryset.annotate(
            comment_count=Count('comments')  # Добавляем количество комментариев
        )

    return posts_queryset
```

**Назначение**: Позволяет отображать количество комментариев к каждому посту без дополнительных запросов к базе данных.

---

## 9. Функция вычисления количества комментариев

Функция для вычисления количества комментариев вынесена в отдельную функцию:

```python
# blog/views.py
def get_posts_with_filters(posts_queryset=None, apply_filters=True, add_comments=True):
    # ...
    if add_comments:
        posts_queryset = posts_queryset.annotate(
            comment_count=Count('comments')
        )
    # ...
    return posts_queryset
```

**Назначение**: Централизует логику фильтрации и добавления количества комментариев, упрощая поддержку кода.

---

## 10. Сортировка после annotate()

После вызова annotate() обязательно вызывается сортировка:

```python
# blog/views.py
class MainPostView(ListView):
    model = Post
    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = get_posts_with_filters(
            apply_filters=True,
            add_comments=True
        ).order_by(*Post._meta.ordering)  # Сортировка после annotate

        context['page_obj'] = get_page_obj(queryset, self.request, paginate_by=10)
        return context
```

**Назначение**: Обеспечивает корректную работу пагинации после добавления новых полей через annotate().

---

## 11. Функция пагинации

Функция пагинации вынесена в отдельную функцию:

```python
# blog/views.py
from django.core.paginator import Paginator

def get_page_obj(queryset, request, paginate_by=10):
    paginator = Paginator(queryset, paginate_by)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
```

**Назначение**: Обеспечивает повторное использование логики пагинации во всех представлениях проекта.

---

## 12. Фильтрация постов для автора

Набор постов на странице автора зависит от посетителя:

```python
# blog/views.py
class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.object
        queryset = user.posts.all()

        apply_filters = self.request.user != user  # Проверяем, является ли посетитель автором

        queryset = get_posts_with_filters(
            queryset,
            apply_filters=apply_filters,
            add_comments=True
        ).order_by(*Post._meta.ordering)

        context['page_obj'] = get_page_obj(queryset, self.request, paginate_by=10)
        return context
```

**Назначение**: Обеспечивает, что только автор может видеть свои неопубликованные посты.

---

## 13. Фильтрация по опубликованности

Фильтрация по опубликованности вынесена в отдельную функцию:

```python
# blog/views.py
def get_posts_with_filters(posts_queryset=None, apply_filters=True, add_comments=True):
    if posts_queryset is None:
        posts_queryset = Post.objects.all()

    if apply_filters:  # Условие для фильтрации
        posts_queryset = posts_queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )

    # ...
    return posts_queryset
```

**Назначение**: Централизует логику фильтрации опубликованных постов, упрощая поддержку и тестирование.

---

## 14. Декоратор @login_required

Контроллеры для создания, редактирования, удаления защищены авторизацией:

```python
# blog/views.py
from django.contrib.auth.mixins import LoginRequiredMixin

class CreatePostView(LoginRequiredMixin, CreateView):
    # ...
    pass

class PostUpdateView(LoginRequiredMixin, UpdateView):
    # ...
    def dispatch(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)

        if request.user != post.author:
            return redirect('blog:post_detail', post_id=post_id)
        return super().dispatch(request, *args, **kwargs)

class PostDeleteView(LoginRequiredMixin, DeleteView):
    # ...
    pass
```

**Назначение**: Обеспечивает, что только авторизованные пользователи могут создавать, редактировать и удалять контент.

---

## 15. Использование redirect() без reverse()

Метод redirect() работает с маршрутами напрямую:

```python
# blog/views.py
class PostUpdateView(LoginRequiredMixin, UpdateView):
    # ...
    def dispatch(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')

        post = get_object_or_404(Post, id=post_id)

        if request.user != post.author:
            return redirect('blog:post_detail', post_id=post_id)  # Напрямую используем имя маршрута
        return super().dispatch(request, *args, **kwargs)

class PostDeleteView(LoginRequiredMixin, DeleteView):
    # ...
    def get_success_url(self):
        return reverse_lazy('blog:profile', args=[self.request.user.username])
```

**Назначение**: Упрощает код и делает его более читаемым, так как redirect() сам разрешает имена маршрутов.

---

## 16. Проверка авторства поста

В контроллере post_detail() проверяется авторство поста:

```python
# blog/views.py
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])

        if self.request.user == post.author:
            return post

        # Второй вызов get_object_or_404 для опубликованных постов
        return get_object_or_404(
            get_posts_with_filters(apply_filters=True, add_comments=False),
            id=self.kwargs['post_id']
        )
```

**Назначение**: Обеспечивает, что неавторы не могут видеть неопубликованные посты, даже если знают их ID.

---

## Раздел 2

## 1. Папки static, static-dev, html не хранятся в git-репозитории

В проекте следуется практике не хранить папки static, static-dev и html в репозитории git:

```gitignore
# .gitignore
static/
static-dev/
html/
```

**Назначение**: Это позволяет поддерживать чистую историю изменений в репозитории, избегать хранения временных файлов и соблюдать лучшие практики разработки Django-приложений.

---

## 2. Форма для поста настраивается через exclude

Форма поста настраивается через exclude, а не fields:

```python
# blog/forms.py
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'created_at')  # Исключаем автора и дату создания
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'datetime-local'}),
            'is_published': forms.CheckboxInput(),
        }
```

**Назначение**: Позволяет избежать случайного включения чувствительных полей в форму редактирования и предотвращает попадание нередактируемого поля created_at в форму.

---

## 3. Функции фильтрации и подсчета комментариев объединены

Функции фильтрации по опубликованности и подсчета комментариев объединены в одну:

```python
# blog/views.py
def get_posts_with_filters(posts_queryset=None, apply_filters=True, add_comments=True):
    if posts_queryset is None:
        posts_queryset = Post.objects.all()

    if apply_filters:
        posts_queryset = posts_queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )

    posts_queryset = posts_queryset.select_related(
        'author', 'category', 'location'
    )

    if add_comments:
        posts_queryset = posts_queryset.annotate(
            comment_count=Count('comments')
        )

    return posts_queryset
```

**Назначение**: Упрощает код и позволяет использовать параметры для включения/выключения фильтрации и подсчета комментариев.

---

## 4. Функция фильтрации принимает набор постов

Функция фильтрации принимает параметром набор постов для фильтрации:

```python
# blog/views.py
def get_posts_with_filters(posts_queryset=None, apply_filters=True, add_comments=True):
    if posts_queryset is None:
        posts_queryset = Post.objects.all()  # Значение по умолчанию

    if apply_filters:
        posts_queryset = posts_queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )
    # ...
    return posts_queryset
```

**Назначение**: Позволяет использовать функцию с любым набором постов, а не только со всеми постами в базе.

---

## 5. Два вызова get_object_or_404() для проверки авторства

В контроллере post_detail() делаются два вызова get_object_or_404():

```python
# blog/views.py
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])  # Первый вызов - из полной таблицы

        if self.request.user == post.author:
            return post

        # Второй вызов - из набора опубликованных постов
        return get_object_or_404(
            get_posts_with_filters(apply_filters=True, add_comments=False),
            id=self.kwargs['post_id']
        )
```

**Назначение**: Обеспечивает проверку, что неавтор может видеть только опубликованные посты.

---

## 6. Использование поля связи для извлечения связанных объектов

Извлечение постов для категории выполняется через поле связи:

```python
# blog/views.py
class CategoryPostView(DetailView):
    model = Category
    template_name = 'blog/category.html'
    slug_url_kwarg = 'category_slug'
    context_object_name = 'category'

    def get_queryset(self):
        return Category.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        posts = self.object.post_set.all()  # Используем поле связи

        queryset = get_posts_with_filters(
            posts,
            apply_filters=True,
            add_comments=True
        ).order_by(*Post._meta.ordering)

        context['page_obj'] = get_page_obj(queryset, self.request, paginate_by=10)
        return context
```

**Назначение**: Позволяет эффективно извлекать связанные объекты без дополнительных фильтров и работает в шаблонах, где вызовы методов с параметрами не поддерживаются.

---

## 7. Сортировка после annotate() с использованием _meta.ordering

После вызова annotate() используется сортировка из модели:

```python
# blog/views.py
queryset = get_posts_with_filters(
    apply_filters=True,
    add_comments=True
).order_by(*Post._meta.ordering)  # Используем сортировку из модели
```

**Назначение**: Обеспечивает согласованность сортировки с настройками модели и избегает необходимости дублировать настройки сортировки.

---

## 8. Использование классов-представлений CreateView и UpdateView

Используются классы-представления, которые автоматически обрабатывают GET и POST:

```python
# blog/views.py
class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('post_list')
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user.username
        })


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    # Обрабатывает и GET, и POST запросы автоматически
```

**Назначение**: Автоматически обрабатывает GET и POST запросы, упрощая код и уменьшая количество необходимых проверок.

---

## 9. Использование UserAdmin для модели пользователя

В проекте используется стандартная модель User Django, но админ-класс для неё не переопределен (используется стандартный).