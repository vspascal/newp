from django import forms
from newp.settings import MAX_IMAGE_SIZE, MAX_MUSIC_SIZE


IS_PRIVATE = [
    (True, True),
    (False, False)
]

MUSIC_TYPE = [
    'mp3',
    'mpeg'
]


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput, required=True)


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    firstname = forms.CharField(max_length=30, required=True)
    lastname = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput, required=True)


class ImageUploadForm(forms.Form):
    profile = forms.ImageField()

    def clean_file(self):
        file = self.cleaned_data['profile']
        if file._size > MAX_IMAGE_SIZE:
            return False
        else:
            return True


class MusicUploadForm(forms.Form):
    music = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data['music']

        file_type = file.content_type.spilt('.')[1]

        if file_type in MUSIC_TYPE:
            if file._size > MAX_MUSIC_SIZE:
                return False
            else:
                return True
        else:
            return False


class BlogForm(forms.Form):
    title = forms.CharField(max_length=100, required=True)
    content = forms.CharField(widget=forms.Textarea, required=True)
    private = forms.ChoiceField(choices=IS_PRIVATE, required=True)
    music = forms.FileField(required=False)

    def clean_file(self):
        try:
            file = self.cleaned_data['music']
            info = file.content_type.split('/')
            file_type = info[1]

            if file_type in MUSIC_TYPE:
                if file._size > MAX_MUSIC_SIZE:
                    return False
                else:
                    return True
            else:
                    return False
        except AttributeError:
            return True


class ForwardForm(forms.Form):
    fwdcontent = forms.CharField(max_length=100)
    fwdprivate = forms.CharField(required=False)


class CommentForm(forms.Form):
    comment_author_id = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)

