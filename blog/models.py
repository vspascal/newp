import datetime
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.utils import timezone


GENDER = (
    ('0', u'Male'),
    ('1', u'Female')
)


DEFAULT_PROFILE_PHOTO = 'static/blog/profile/default.jpg'


def user_directory_path(instance, filename):
    date = timezone.now().time()
    return 'static/blog/profile/{0}/{1}.jpg'.format(instance.id, date)


def music_directory_path(instance, filename):
    return 'static/blog/music/{0}'.format(filename)


class User(AbstractUser):
    gender = models.CharField(max_length=1, default='0', choices=GENDER)
    follow = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Relationship',
        through_fields=('from_user', 'to_user')
    )
    profile_photo = models.ImageField(
        upload_to=user_directory_path,
        default=DEFAULT_PROFILE_PHOTO,
        blank=True
    )

    class Meta:
        ordering = ['date_joined']


class Relationship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='from_user'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='to_user'
    )
    reviewed = models.BooleanField(default=False)
    add_date = models.DateTimeField('Date added.')


class Music(models.Model):
    singer = models.CharField(max_length=50, null=True)
    song_name = models.CharField(max_length=100, null=True)
    music = models.FileField(
        upload_to=music_directory_path,
        null=True
    )


class Blog(models.Model):
    blog_title = models.CharField(max_length=100)
    blog_content = models.TextField(blank=True, null=True)
    blog_postdate = models.DateTimeField("Date posted")
    blog_private = models.BooleanField(default=False)
    popularity = models.IntegerField(default=0)
    liked_user = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='LikeRelationship'
    )
    blog_author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blog_author"
    )
    relate_music = models.ForeignKey(
        Music,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fwd_blog = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name="forward_blog",
        null=True
    )
    fwd_viewed = models.BooleanField(default=False)
    like_count = models.IntegerField(default=0)
    forward_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-blog_postdate']

    # def __str__(self):
    #     return "Title: " + self.blog_title + "; Author: " + User.objects.get(pk=self.blog_author_id).__str__()


class LikeRelationship(models.Model):
    to_blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    to_author = models.IntegerField(default=0)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    """docstring for Comment"""
    comment_author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    comment_content = models.TextField(blank=True, null=False)
    comment_date = models.DateTimeField("Date commented.", auto_now_add=True)
    viewed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-comment_date']

    # def __str__(self):
    #     return "User: " + User.objects.get(
    #         pk=self.comment_author_id).user_name + "; " + "Comment on blog: " + Blog.objects.get(
    #         pk=self.comment_blog_id).blog_title + "."

