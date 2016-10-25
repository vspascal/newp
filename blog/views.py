from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render, get_object_or_404, Http404
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic import View, ListView
from django.views.generic.edit import ContextMixin
from django.core.exceptions import PermissionDenied

from .models import Blog, Comment, User, Music, Relationship, LikeRelationship
from .forms import BlogForm, LoginForm, RegisterForm, ImageUploadForm, MusicUploadForm, CommentForm, ForwardForm


# Create your views here.
def get_music_information(music):
    information = music.content_type.split('-')
    return information


class BaseMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(BaseMixin, self).get_context_data(**kwargs)

        if self.request.user.is_active:
            log_user = User.objects.get(pk=self.request.user.id)
            context['log_user'] = log_user
            context['following_count'] = Relationship.objects.filter(from_user=log_user).count()
            context['follower_count'] = Relationship.objects.filter(to_user=log_user).count()
        else:
            context['log_user'] = None

        context['popularity'] = Blog.objects.filter(blog_private=False).order_by('-popularity', '-id')[0:5]

        return context


# URL name = 'index'
class IndexView(BaseMixin, ListView):
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        blog = Blog.objects.none()

        if self.request.user.is_active:
            user = context['log_user']
            context['follow_list'] = user.follow.all()

            for user in user.follow.all():
                blog = blog | Blog.objects.filter(blog_author=user, blog_private=False)

        context['blog_list'] = blog
        return context

    def get_queryset(self):
        return User.objects.all()


# URL name = 'usercontrol'
class UserControlView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'register':
            return render(self.request, 'blog/register.html')
        elif slug == 'manage':
            return self.to_manage_page(self.request)
        elif slug == 'following':
            return self.following_detail(self.request)
        elif slug == 'follower':
            return self.follower_detail(self.request)
        raise PermissionDenied

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'login':
            return self.login()
        elif slug == 'logout':
            return self.logout()
        elif slug == 'register':
            return self.register()
        elif slug == 'search':
            return self.search()
        elif slug == 'manage':
            return self.manage(self.request)

        raise PermissionDenied

    def login(self):
        try:
            next_page = self.request.POST['next']
        except KeyError:
            next_page = self.request.META['HTTP_REFERER']

        form = LoginForm(self.request.POST)

        if form.is_valid():
            name = form.cleaned_data['username']
            pwd = form.cleaned_data['password']
            user = authenticate(username=name, password=pwd)

            if user is not None:
                self.request.session.set_expiry(0)
                login(self.request, user)

        return HttpResponseRedirect(next_page)

    def logout(self):
        logout(self.request)
        next_page = self.request.META['HTTP_REFERER']

        return HttpResponseRedirect(next_page)

    def register(self):
        form = RegisterForm(self.request.POST)

        if form.is_valid():
            user_name = form.cleaned_data['username']
            firstname = form.cleaned_data['firstname']
            lastname = form.cleaned_data['lastname']
            pwd = form.cleaned_data['password']
            e_mail = form.cleaned_data['email']
            user = User.objects.create(username=user_name, first_name=firstname, last_name=lastname, email=e_mail)
            user.set_password(pwd)
            try:
                user.save()
                user = authenticate(username=user_name, password=pwd)
                login(self.request, user)
            except Exception:
                return render(self.request, 'blog/register.html')
            else:
                pass

        return HttpResponseRedirect(reverse('blog:index'))

    @method_decorator(login_required)
    def to_manage_page(self, request):
        context = super(UserControlView, self).get_context_data()

        return render(self.request, 'blog/upload_profile.html', context)

    @method_decorator(login_required)
    def manage(self, request):
        form = ImageUploadForm(self.request.POST, self.request.FILES)
        context = self.get_context_data()

        if form.is_valid():
            if form.clean_file():
                log_user = context['log_user']
                log_user.profile_photo = form.cleaned_data['profile']
                log_user.save()
            else:
                context['error_message'] = 'Image too large'
                return render(self.request, 'blog/upload_profile.html', context)
        else:
            context['error_message'] = 'Submit file is nor an image.'
            return render(self.request, 'blog/upload_profile.html', context)

        return HttpResponseRedirect(reverse('blog:index'))

    @method_decorator(login_required)
    def following_detail(self, request):
        context = self.get_context_data()
        log_user = context['log_user']
        context['type'] = 'Following'
        context['relationships'] = log_user.follow.all()

        return render(self.request, 'blog/relationship.html', context)

    @method_decorator(login_required)
    def follower_detail(self, request):
        context = self.get_context_data()
        log_user = context['log_user']
        context['type'] = 'Follower'
        context['relationships'] = Relationship.objects.select_related('from_user').filter(to_user=log_user)

        return render(self.request, 'blog/relationship.html', context)

    def search(self):
        context = self.get_context_data()
        keyword = self.request.POST['keyword']
        blog = Blog.objects.filter(blog_title__contains=keyword, blog_private=False)
        user = User.objects.filter(username__contains=keyword)

        context['result_blog'] = blog
        context['result_user'] = user

        return render(self.request, 'blog/searchresult.html', context)


# URL name = 'news'
class NewsView(BaseMixin, TemplateView):
    template_name = 'blog/messages.html'

    def get_context_data(self, **kwargs):
        context = super(NewsView, self).get_context_data()
        log_user = context['log_user']
        context['like_news_count'] = LikeRelationship.objects.filter(to_author=log_user.id, viewed=False).count()
        context['comment_news_count'] = Comment.objects.filter(comment_blog__blog_author=log_user, viewed=False).count()
        context['forward_news_count'] = Blog.objects.filter(fwd_blog__blog_author=log_user, fwd_viewed=False).count()
        context['follow_news_count'] = Relationship.objects.filter(to_user=log_user,  reviewed=False).count()

        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        return render(self.request, 'blog/messages.html', context)


# URL name = 'detailnews'
class DetailNewsView(BaseMixin, TemplateView):
    template_name = 'blog/detailnews.html'

    def get_context_data(self, **kwargs):
        context = super(DetailNewsView, self).get_context_data()
        slug = self.kwargs.get('slug')
        log_user = context['log_user']

        if slug == 'likes':
            context['name'] = 'likes'
            news = LikeRelationship.objects.filter(to_author=log_user.id, viewed=False)
            context['news'] = list(news)
            news.update(viewed=True)
            log_user.like_news = F('like_news') - len(context['news'])
        elif slug == 'comments':
            context['name'] = 'comments'
            news = Comment.objects.filter(comment_blog__blog_author_id=log_user.id, viewed=False)
            context['news'] = list(news)
            news.update(viewed=True)
            log_user.comment_news = F('comment_news') - len(context['news'])
        elif slug == 'forwards':
            context['name'] = 'forward'
            news = Blog.objects.filter(fwd_blog__blog_author=log_user, fwd_viewed=False)
            context['news'] = list(news)
            news.update(fwd_viewed=True)
            log_user.forward_news = F('forward_news') - len(context['news'])
        elif slug == 'follows':
            context['name'] = 'follows'
            news = Relationship.objects.filter(to_user=log_user, reviewed=False)
            context['news'] = list(news)
            news.update(reviewed=True)
            log_user.follow_news = F('follow_news') - len(context['news'])
        else:
            raise Http404

        log_user.save()

        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        return render(self.request, 'blog/detailnews.html', context)


# URL name = 'user'
class UserView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'homepage':
            return self.homepage()
        elif slug == 'follow':
            home_id = self.kwargs.get('u_id')

            return HttpResponseRedirect(reverse('blog:user', kwargs={'u_id': home_id, 'slug': 'homepage'}))
        else:
            return Http404

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'follow':
            return self.follow(self.request)
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        log_user = context['log_user']
        home_id = self.kwargs.get('u_id')
        user = get_object_or_404(User, pk=home_id)
        blog_list = Blog.objects.filter(blog_author=user)

        if type(log_user) is User:
            context['follow'] = user in log_user.follow.all()

            if home_id == str(log_user.id):
                is_self = True
            else:
                is_self = False
                blog_list = blog_list.filter(blog_private=False)
                try:
                    context['follow'] = user in log_user.follow.all()
                except AttributeError:
                    context['follow'] = False

        else:
            is_self = False
            context['follow'] = False
            blog_list = blog_list.filter(blog_private=False)

        context['User'] = user
        context['Blog_list'] = blog_list
        context['self'] = is_self

        return context

    def homepage(self):
        context = self.get_context_data()

        return render(self.request, 'blog/personalhomepage.html', context)

    @method_decorator(login_required)
    def follow(self, request):
        context = self.get_context_data()
        added_user = context['User']
        log_user = context['log_user']

        if not context['follow']:
            relationship = Relationship.objects.create(
                from_user=log_user,
                to_user=added_user,
                add_date=timezone.now()
            )
            relationship.save()
            added_user.save()
            context['follow'] = True
        else:
            Relationship.objects.filter(from_user=log_user, to_user=added_user).delete()
            added_user.save()
            context['follow'] = False

        try:
            next_page = self.request.POST['next_page']
        except KeyError:
            pass
        else:
            if next_page == 'following':
                return HttpResponseRedirect(reverse('blog:usercontrol', kwargs={'slug': 'following'}))
            elif next_page == 'follower':
                return HttpResponseRedirect(reverse('blog:usercontrol', kwargs={'slug': 'follower'}))
            else:
                raise Http404

        return HttpResponseRedirect(
            reverse('blog:user', kwargs={'u_id': added_user.id, 'slug': 'homepage'}))


# URL name = writeblog
class WriteBlogView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(WriteBlogView, self).get_context_data(**kwargs)

        return context

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        form = BlogForm()
        context = self.get_context_data()
        context['form'] = form

        return render(self.request, 'blog/blog_form.html', context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = BlogForm(self.request.POST, self.request.FILES)
        context = self.get_context_data()

        if form.is_valid():
            if form.clean_file():
                title = form.cleaned_data['title']
                content = form.cleaned_data['content']
                private = form.cleaned_data['private']
                music = form.cleaned_data['music']
                m = Music.objects.create()
                m.music = music
                m.save()
                post_date = timezone.now()
                author = self.request.user.id
                blog = Blog.objects.create(blog_title=title, blog_content=content, blog_postdate=post_date,
                                           blog_author_id=author, blog_private=private)
                blog.relate_music = m
                try:
                    blog.save()
                except Exception:
                    return render(reverse('blog:writeblog'))
                else:
                    return HttpResponseRedirect(reverse('blog:blog', kwargs={'b_id': blog.id, 'slug': 'view'}))
            else:
                context['error_message'] = 'Music file too large.'
                return HttpResponseRedirect(reverse('blog:writeblog'))
        else:
            return HttpResponseRedirect(reverse('blog:writeblog'))


# URL name = 'blog'
class BlogView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'view':
            return self.view()
        else:
            blog_id = self.kwargs.get('b_id')
            return HttpResponseRedirect(reverse('blog:blog', kwargs={'b_id': blog_id, 'slug': 'view'}))

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'delete':
            return self.deleteblog()
        elif slug == 'like':
            return self.like(self.request)
        elif slug == 'forward':
            return self.forward(self.request)
        elif slug == 'comment':
            return self.comment(self.request)

    def get_context_data(self, *args, **kwargs):
        context = super(BlogView, self).get_context_data(**kwargs)
        log_user = context['log_user']
        b_id = self.kwargs.get('b_id')
        blog = Blog.objects.get(pk=b_id)
        home_id = blog.blog_author_id
        user = get_object_or_404(User, pk=home_id)

        if type(log_user) is User:

            if home_id == log_user.id:
                is_self = True
            else:
                is_self = False

            context['liked'] = blog.liked_user.filter(pk=log_user.id).exists()
        else:
            is_self = False
            context['liked'] = False

        context['blog'] = blog
        context['User'] = user
        context['self'] = is_self
        context['comment_list'] = blog.comment_set.all()
        if user == log_user:
            context['comment_list'].update(viewed=True)

        if blog.relate_music is not None:
            context['music'] = blog.relate_music.music

        return context

    def view(self):
        context = self.get_context_data()
        blog = context['blog']
        blog.view_count = F('view_count') + 1
        blog.save()
        blog.refresh_from_db()
        context['blog'] = blog

        return render(self.request, 'blog/viewblog.html', context)

    @method_decorator(login_required)
    def forward(self, request):
        context = self.get_context_data()
        blog = context['blog']
        log_user = context['log_user']

        form = ForwardForm(self.request.POST)

        if form.is_valid():
            fwdcontent = form.cleaned_data['fwdcontent']
            fwdprivate = form.cleaned_data['fwdprivate']
            fwddate = timezone.now()
            fwdblog = Blog(
                blog_author=log_user,
                blog_title=fwdcontent,
                blog_postdate=fwddate,
                blog_private=fwdprivate,
                fwd_blog=blog,
                relate_music=blog.relate_music
            )
            if not fwdprivate:
                fwdblog.fwd_viewed = True

            fwdblog.save()
            blog.popularity = F('popularity') + 1
            blog.forward_count = F('forward_count') + 1
            blog.blog_author.save()
            blog.save()

        return HttpResponseRedirect(reverse('blog:blog', kwargs={'b_id': blog.id, 'slug': 'view'}))

    @method_decorator(login_required)
    def like(self, request):
        context = self.get_context_data()
        blog = context['blog']
        log_user = context['log_user']
        log_user_id = log_user.id

        if log_user_id != blog.blog_author_id:
            if blog.liked_user.filter(pk=log_user_id).exists():
                LikeRelationship.objects.get(to_blog=blog, from_user=log_user).delete()
                blog.popularity = F('popularity') - 1
                blog.like_count = F('like_count') - 1
                blog.save()
                blog.blog_author.save()
            else:
                LikeRelationship.objects.create(to_blog=blog,
                                                from_user=log_user,
                                                to_author=blog.blog_author.id).save()
                blog.popularity = F('popularity') + 1
                blog.like_count = F('like_count') + 1
                blog.save()
                blog.blog_author.save()

        return HttpResponseRedirect(reverse('blog:blog', kwargs={'b_id': blog.id, 'slug': 'view'}))

    def deleteblog(self):
        context = self.get_context_data()
        blog = context['blog']
        log_user = context['log_user']
        if blog.blog_author_id == log_user.id:
            Blog.objects.get(pk=blog.id).delete()
            context['blog'] = None
            context['follow'] = False
            context['Blog_list'] = Blog.objects.filter(blog_author=log_user)

        context['comment_list'] = None
        context['music'] = None

        return HttpResponseRedirect(reverse('blog:user', kwargs={'u_id': log_user.id, 'slug': 'homepage'}))

    @method_decorator(login_required)
    def comment(self, request):
        context = self.get_context_data()
        blog = context['blog']
        form = CommentForm(self.request.POST)

        if form.is_valid():
            author_id = form.cleaned_data['comment_author_id']
            content = form.cleaned_data['content']
            date = timezone.now()
            comment = Comment(comment_author_id=author_id, comment_blog=blog, comment_content=content,
                              comment_date=date)
            try:
                comment.save()
                blog.popularity = F('popularity') + 1
                blog.comment_count = F('comment_count') + 1
                blog.blog_author.save()
                blog.save()
            except Exception:
                raise Http404
            else:
                context['comment_list'] = blog.comment_set.all()

        return HttpResponseRedirect(reverse('blog:blog', kwargs={'b_id': blog.id, 'slug': 'view'}))


# URL name = 'comment'
class DeleteCommentView(BaseMixin, View):
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        c_id = self.kwargs.get('c_id')
        blog = context['blog']

        if context['self']:
            Comment.objects.get(pk=c_id).delete()
            context['comment_list'] = blog.comment_set.all()
            blog.comment_count = F('comment_count') - 1

        return HttpResponseRedirect(reverse('blog:blog', kwargs={'b_id': blog.id, 'slug': 'view'}))

    def get_context_data(self, *args, **kwargs):
        context = super(DeleteCommentView, self).get_context_data(**kwargs)
        log_user = context['log_user']
        c_id = self.kwargs.get('c_id')
        comment = Comment.objects.get(pk=c_id)
        b_id = comment.comment_blog.id
        blog = Blog.objects.get(pk=b_id)
        home_id = blog.blog_author_id
        user = get_object_or_404(User, pk=home_id)

        if home_id == log_user.id:
            is_self = True
        else:
            is_self = False

        context['liked'] = blog.liked_user.filter(pk=log_user.id).exists()
        context['blog'] = blog
        context['User'] = user
        context['self'] = is_self
        context['comment_list'] = blog.comment_set.all()

        return context
