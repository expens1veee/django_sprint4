from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (ListView, CreateView, UpdateView,
                                  DetailView, DeleteView)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from .forms import UserUpdateForm, PostForm, CommentForm
from .models import Category, Post, User, Comment
from django.utils import timezone


def get_posts_with_filters(posts_queryset=None,
                           apply_filters=True, add_comments=True):
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


def get_page_obj(queryset, request, paginate_by=10):
    paginator = Paginator(queryset, paginate_by)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


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

        apply_filters = self.request.user != user

        queryset = get_posts_with_filters(
            queryset,
            apply_filters=apply_filters,
            add_comments=True
        ).order_by(*Post._meta.ordering)

        context['page_obj'] = get_page_obj(
            queryset,
            self.request,
            paginate_by=10)

        return context


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


class MainPostView(ListView):
    model = Post
    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = get_posts_with_filters(
            apply_filters=True,
            add_comments=True
        ).order_by(*Post._meta.ordering)

        context['page_obj'] = get_page_obj(
            queryset,
            self.request,
            paginate_by=10)

        return context


class CategoryPostView(DetailView):
    model = Category
    template_name = 'blog/category.html'
    slug_url_kwarg = 'category_slug'
    context_object_name = 'category'

    def get_queryset(self):
        return Category.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        posts = self.object.post_set.all()

        queryset = get_posts_with_filters(
            posts,
            apply_filters=True,
            add_comments=True
        ).order_by(*Post._meta.ordering)

        context['page_obj'] = get_page_obj(
            queryset,
            self.request,
            paginate_by=10)

        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    form_class = UserUpdateForm

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user.username
        })


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')

        post = get_object_or_404(Post, id=post_id)

        if request.user != post.author:
            return redirect('blog:post_detail', post_id=post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.id})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def dispatch(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')

        post = get_object_or_404(Post, id=post_id)

        if request.user != post.author:
            return redirect('blog:post_detail', post_id=post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:profile', args=[self.request.user.username])


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, id=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        return context

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment_id = self.kwargs.get('comment_id')

        comment = get_object_or_404(Comment, id=comment_id)

        if request.user != comment.author:
            return redirect('blog:post_detail', post_id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment_id = self.kwargs.get('comment_id')

        comment = get_object_or_404(Comment, id=comment_id)

        if request.user != comment.author:
            return redirect('blog:post_detail', post_id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id})
