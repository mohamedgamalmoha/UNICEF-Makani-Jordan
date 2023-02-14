import csv
from typing import List

from django.db.models import Model, QuerySet
from django.contrib import messages
from django.contrib.auth import get_permission_codename
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import View, ContextMixin
from django.http.response import HttpResponseBase
from django.http import HttpResponse, HttpResponseForbidden


class BaseView(ContextMixin, View):
    response_class: HttpResponseBase = HttpResponse
    content_type: str

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def render_to_response(self, context, **response_kwargs) -> HttpResponseBase:
        response_kwargs.setdefault('content_type', self.content_type)
        return self.response_class(request=self.request, context=context, **response_kwargs)


class ModelCSVResponse(BaseView):

    model: Model
    csv_queryset: QuerySet = None
    csv_ordering: str = None

    csv_columns: List[str] = []
    csv_extra_columns: List[str] = []
    csv_fields: List[str] = []
    csv_exclude_fields: List[str] = []
    csv_extra_fields: List[str] = []

    csv_file_name: str = None
    content_type: str = 'text/csv'

    def init(self, model, **kwargs):
        """Custom initialization for new instance."""
        if not model:
            raise ValueError('model must be entered')
        self.model = model
        for key, val in kwargs.items():
            if hasattr(self, key) and val:
                setattr(self, key, val)

    def get_csv_fields(self) -> List[str]:
        """Return model field or fields without excluded ones."""
        fields = self.csv_fields or list(map(lambda field: field.name, self.model._meta.fields))
        fields.extend(self.csv_extra_fields)
        lst_fields = filter(lambda field_name: field_name not in self.csv_exclude_fields, fields)
        return list(lst_fields)

    def get_csv_queryset(self, queryset=None) -> QuerySet:
        """Return ordering queryset - in case csv_ordering is specified - to use for writing csv file."""
        queryset = queryset or self.csv_queryset or self.model._default_manager.all()

        if queryset is None:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.csv_queryset, or override "
                "%(cls)s.get_csv_queryset()." % {
                    'cls': self.__class__.__name__
                }
            )

        ordering = self.get_csv_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering, )
            queryset = queryset.order_by(*ordering)

        return queryset

    def get_csv_columns(self) -> List[str]:
        """Return csv columns."""
        lst = self.csv_columns or self.get_csv_fields()
        lst.extend(self.csv_extra_columns)
        return lst

    def get_csv_rows(self) -> List[List[str]]:
        """Return csv rows."""
        return [[getattr(obj, field) for field in self.get_csv_fields()] for obj in self.get_csv_queryset().all()]

    def get_csv_file_name(self) -> str:
        """Return csv filename."""
        return self.csv_file_name or self.model._meta.model_name

    def get_csv_ordering(self) -> str:
        """Return the field or fields to use for ordering the queryset."""
        return self.csv_ordering

    def handle_response(self, **response_kwargs):
        """It handles the response in case if it needs to be updated."""
        response_kwargs.setdefault('content_type', self.content_type)
        response = self.response_class(**response_kwargs)
        response['Content-Disposition'] = f'attachment; filename="{self.get_csv_file_name()}.csv"'
        return response

    @staticmethod
    def write_csv(response, headers, rows):
        """It handles the writing of csv file."""
        writer = csv.writer(response)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return response

    def render_to_response(self, context: dict = None, **response_kwargs):
        """Return csv file response."""
        rows = self.get_csv_rows()
        columns = self.get_csv_columns()
        response = self.handle_response(**response_kwargs)
        return self.write_csv(response, columns, rows)


class BaseRelationalModelCSVResponse(ModelCSVResponse):
    csv_object_related_field_name: str = None
    csv_object_related_fields: List[str] = None

    def get_csv_object_related(self, obj) -> QuerySet:
        """Get all relational objects."""
        return getattr(obj, self.csv_object_related_field_name, None)

    def get_csv_columns(self) -> List[str]:
        """Add related fields to columns."""
        columns = super().get_csv_columns()
        columns.extend(self.csv_object_related_fields)
        return list(map(lambda st: str.capitalize(st), columns))

    def get_csv_rows(self) -> List[List[str]]:
        """Return csv rows."""
        rows_lst = []
        for obj in self.get_csv_queryset().all():

            # Get model fields for each instance
            fields_lst = [value() if callable(value := getattr(obj, field)) else value for field in
                          self.get_csv_fields()]

            # Get model related fields for each instance
            related_object = self.get_csv_object_related(obj)
            if related_object is not None:
                fields_lst.extend([value() if callable(value := getattr(related_object, related_field)) else value
                                   for related_field in self.csv_object_related_fields])

            # Append to rows list
            rows_lst.append(fields_lst)
        return rows_lst


class ModelCSVResponseAdmin(BaseRelationalModelCSVResponse):
    csv_dropdown_label: str = "Export As CSV"
    csv_allow_warning_message: bool = True
    csv_warning_message: str = 'Data downloaded, be careful it might be sensitive'

    def has_csv_permission(self, request):
        """Does the user have the publish permission?"""
        opts = self.opts
        codename = get_permission_codename('csv', opts)
        return request.user.has_perm('%s.%s' % (opts.app_label, codename))

    def export_csv(self, request, queryset):
        if not self.has_csv_permission(request):
            return HttpResponseForbidden()

        self.csv_queryset = queryset
        if self.csv_allow_warning_message:
            self.message_user(request, self.csv_warning_message, messages.WARNING)

        self.message_user(request, f'{self.csv_queryset.count()} of {self.model._meta.model_name} '
                                   f'was successfully downloaded as csv.', messages.SUCCESS)
        return self.render_to_response()

    export_csv.allowed_permissions = ('csv',)
    export_csv.short_description = csv_dropdown_label


def cls_to_func_csv_action(model: Model, csv_class: ModelCSVResponse = ModelCSVResponse, csv_queryset: QuerySet = None,
                           csv_ordering: str = None, csv_file_name: str = None, csv_extra_columns=None,
                           csv_exclude_fields=None):
    """Turn CSV class to function to be used more than once"""

    if csv_extra_columns is None:
        csv_extra_columns = []

    if csv_exclude_fields is None:
        csv_exclude_fields = []

    response = csv_class()
    response.init(model,  csv_queryset=csv_queryset, csv_ordering=csv_ordering, csv_file_name=csv_file_name,
                  csv_extra_columns=csv_extra_columns, csv_exclude_fields=csv_exclude_fields)
    return response.render_to_response()
