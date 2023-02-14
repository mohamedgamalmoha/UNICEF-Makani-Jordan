from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Teacher(models.Model):
    name = models.CharField(max_length=60)
    center = models.CharField(max_length=60)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Facilitator'
        verbose_name_plural = 'Facilitators'
        ordering = ('-created', )


class FollowingUp(models.Model):
    teacher = models.ForeignKey(Teacher,  on_delete=models.SET_NULL, null=True, related_name='followings', verbose_name='Facilitator')
    grade = models.IntegerField(null=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    lesson = models.CharField(max_length=60, null=True)
    notes = models.TextField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = 'Follow Up'
        verbose_name_plural = 'Follow Ups'
        ordering = ('-created', )
