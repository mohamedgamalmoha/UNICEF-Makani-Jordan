from django import forms

from .models import FollowingUp


class UpdateCSSClassFormMixin:
    css_class: str = 'form-control'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize Fields - css class -
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = self.css_class


class FollowingUpForm(UpdateCSSClassFormMixin, forms.ModelForm):

    class Meta:
        model = FollowingUp
        fields = ('teacher', 'grade', 'lesson', 'notes', 'link')
        labels = {'teacher': 'Facilitator'}
