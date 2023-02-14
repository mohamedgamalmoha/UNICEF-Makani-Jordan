from django.contrib import admin

from .models import Teacher, FollowingUp
from .admin_csv import ModelCSVResponseAdmin


class TeacherModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created', 'updated')
    readonly_fields = ('created', 'updated')
    search_fields = ('name', 'center')
    list_filter = ('created', 'updated')
    date_hierarchy = 'created'


class FollowingUpModelAdmin(admin.ModelAdmin, ModelCSVResponseAdmin):
    list_display = ('teacher', 'grade', 'created', 'updated')
    readonly_fields = ('created', 'updated')
    search_fields = ('teacher__name', 'teacher__center')
    list_filter = ('created', 'updated', 'teacher')
    date_hierarchy = 'created'
    actions = ('export_csv', )

    # csv options
    csv_exclude_fields = ('id', 'teacher', 'updated')
    csv_object_related_field_name = 'teacher'
    csv_object_related_fields = ('center', )

    def get_csv_columns(self):
        columns = super(FollowingUpModelAdmin, self).get_csv_columns()
        columns[columns.index('Created')] = 'Date of visit'
        return columns


admin.site.register(Teacher, TeacherModelAdmin)
admin.site.register(FollowingUp, FollowingUpModelAdmin)
