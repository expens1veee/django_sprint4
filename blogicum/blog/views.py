from typing import Any
from unicodedata import category

from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template.context_processors import request
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import UserUpdateForm, PostForm, CommentForm
from .models import Category, Post, User, Comment
from django.utils import timezone


class ProfileView(ListView):
    model = Post
    ordering = 'id'
    paginate_by = 10
    template_name = 'blog/profile.html'

    def get_queryset(self):
        username = self.kwargs.get('username')
        user = get_object_or_404(User, username=username)

        queryset = Post.objects.filter(author=user)
        if self.request.user != user:
            queryset = queryset.filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True
            )

        return queryset.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(User, username=self.kwargs.get('username'))
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
        return reverse_lazy('blog:profile', kwargs={
            'username': self.request.user.username
        })

class MainPostView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).select_related(
            'author', 'category', 'location'
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')


class CategoryPostView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = 10


    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')

        self.category = get_object_or_404(Category, slug=category_slug, is_published=True)

        return Post.objects.filter(
            category=self.category,
            is_published = True,
            pub_date__lte=timezone.now()
        ).select_related(
            'author', 'category'
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:profile')
    form_class = UserUpdateForm

    def get_object(self):
        return self.request.user


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):
        post_id = self.kwargs.get('id')

        post = get_object_or_404(Post, id=post_id)

        user = self.request.user

        if not post.is_published:
            if user.is_authenticated and user == post.author:
                return post
            else:
                raise Http404("Пост не найден")

        if post.pub_date > timezone.now():
            if user.is_authenticated and user == post.author:
                return post
            else:
                raise Http404("Пост еще не опубликован")

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'id'

    def dispatch(self, request, *args, **kwargs):
        post_id = self.kwargs.get('id')

        post = get_object_or_404(Post, id=post_id)

        if request.user != post.author:
            return redirect('blog:post_detail', id=post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'id': self.object.id})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def dispatch(self, request, *args, **kwargs):
        post_id = self.kwargs.get('id')

        post = get_object_or_404(Post, id=post_id)

        if request.user != post.author:
            return redirect('blog:post_detail', id=post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:profile', args=[self.request.user.username])


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, id=self.kwargs['id'])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        return context

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'id': self.object.post.id})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment_id = self.kwargs.get('comment_id')

        comment = get_object_or_404(Comment, id=comment_id)

        if request.user != comment.author:
            return redirect('blog:post_detail', id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'id': self.object.post.id})

class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment_id = self.kwargs.get('comment_id')

        comment = get_object_or_404(Comment, id=comment_id)

        if request.user != comment.author:
            return redirect('blog:post_detail', id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'id': self.object.post.id})