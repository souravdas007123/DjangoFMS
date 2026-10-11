import csv

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import FieldDoesNotExist, PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, models, transaction
from django.db.models import ProtectedError, Q, RestrictedError
from django.forms import inlineformset_factory, modelform_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.cache import patch_vary_headers
from django.views import View

from . import registry
from .forms import StyledModelForm
from .helpers import display, label_for

PAGE_SIZE = 20
EXPORT_LIMIT = 20000
STAT_PROPERTIES = (
    "total_amount", "yield_percent", "downtime_hours", "total_cost", "profit_per_unit", "value",
)
INLINE_EXTRA_PROPERTIES = ("amount", "pending_quantity")
HIDDEN_INLINE_FIELDS = {"id", "created_at", "updated_at", "is_active"}


class ModelView(AccessMixin, View):
    """Resolves the model from the URL and enforces Django model permissions."""

    permission_action = "view"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.cfg = registry.get_config(kwargs["app_label"], kwargs["model_name"])
        if not request.user.has_perm(self.cfg.perm(self.permission_action)):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def base_context(self, **extra):
        cfg, user = self.cfg, self.request.user
        context = {
            "cfg": cfg,
            "can_add": user.has_perm(cfg.perm("add")),
            "can_change": user.has_perm(cfg.perm("change")),
            "can_delete": user.has_perm(cfg.perm("delete")),
        }
        context.update(extra)
        return context


# --------------------------------------------------------------------- list
class ListPage(ModelView):
    permission_action = "view"

    def get(self, request, app_label, model_name):
        cfg = self.cfg
        qs = cfg.model._default_manager.all()

        fk_names = [n for n in cfg.list_display if cfg.is_fk(n)]
        if fk_names:
            qs = qs.select_related(*fk_names)

        query = request.GET.get("q", "").strip()
        if query and cfg.search_fields:
            cond = Q()
            for field_name in cfg.search_fields:
                cond |= Q(**{f"{field_name}__icontains": query})
            qs = qs.filter(cond)

        filters = self.apply_filters(request, qs)
        qs = filters["qs"]

        ordering = request.GET.get("o", "")
        sort_key = ordering.lstrip("-")
        if sort_key and cfg.is_sortable(sort_key) and sort_key in cfg.list_display:
            qs = qs.order_by(ordering)
        else:
            ordering = ""
        if not qs.ordered:
            qs = qs.order_by("-pk")

        if request.GET.get("export") == "csv":
            return self.export_csv(qs)

        paginator = Paginator(qs, PAGE_SIZE)
        page = paginator.get_page(request.GET.get("page"))

        def url_with(**updates):
            params = request.GET.copy()
            for key, value in updates.items():
                if value is None:
                    params.pop(key, None)
                else:
                    params[key] = value
            encoded = params.urlencode()
            return f"?{encoded}" if encoded else "?"

        columns = []
        for name in cfg.list_display:
            sortable = cfg.is_sortable(name)
            direction = None
            if sort_key == name:
                direction = "desc" if ordering.startswith("-") else "asc"
            next_order = f"-{name}" if ordering == name else name
            columns.append({
                "name": name,
                "label": label_for(cfg.model, name),
                "sortable": sortable,
                "direction": direction,
                "url": url_with(o=next_order, page=None) if sortable else "",
            })

        can_change = request.user.has_perm(cfg.perm("change"))
        can_delete = request.user.has_perm(cfg.perm("delete"))
        rows = []
        for obj in page.object_list:
            rows.append({
                "cells": [display(obj, name) for name in cfg.list_display],
                "detail_url": cfg.detail_url(obj.pk),
                "edit_url": cfg.update_url(obj.pk) if can_change else "",
                "delete_url": cfg.delete_url(obj.pk) if can_delete else "",
            })

        page_links = []
        for number in paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1):
            if number == paginator.ELLIPSIS:
                page_links.append({"label": "…", "url": "", "active": False})
            else:
                page_links.append({"label": number, "url": url_with(page=str(number)), "active": number == page.number})

        context = self.base_context(
            page=page,
            rows=rows,
            columns=columns,
            page_links=page_links,
            prev_url=url_with(page=str(page.previous_page_number())) if page.has_previous() else "",
            next_url=url_with(page=str(page.next_page_number())) if page.has_next() else "",
            query=query,
            ordering=ordering,
            filter_controls=filters["controls"],
            has_filters=bool(query or filters["active"]),
            reset_url=request.path,
            export_url=url_with(export="csv", page=None),
            list_url=cfg.list_url,
            colspan=len(columns) + 1,
        )
        template = "ui/_results.html" if request.headers.get("HX-Request") == "true" else "ui/list.html"
        response = render(request, template, context)
        patch_vary_headers(response, ["HX-Request"])
        return response

    def apply_filters(self, request, qs):
        controls = []
        active = False
        for spec in self.cfg.filters:
            field = self.cfg.field(spec.name)
            value = request.GET.get(f"f_{spec.name}", "")
            if value != "":
                lookup = (value == "1") if spec.kind == "bool" else value
                try:
                    qs = qs.filter(**{spec.name: lookup})
                    active = True
                except (ValueError, TypeError, ValidationError):
                    value = ""
            if spec.kind == "choices":
                options = [(str(v), str(label)) for v, label in field.choices]
            elif spec.kind == "bool":
                options = [("1", "Yes"), ("0", "No")]
            else:
                related = field.remote_field.model._default_manager.all()[:200]
                options = [(str(o.pk), str(o)) for o in related]
            controls.append({"name": f"f_{spec.name}", "label": spec.label, "value": value, "options": options})
        return {"qs": qs, "controls": controls, "active": active}

    def export_csv(self, qs):
        cfg = self.cfg
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{cfg.model_name}.csv"'
        response.write("﻿")  # BOM so Excel opens UTF-8 correctly
        writer = csv.writer(response)
        writer.writerow([label_for(cfg.model, n) for n in cfg.list_display])
        for obj in qs[:EXPORT_LIMIT]:
            writer.writerow([display(obj, n)["text"] for n in cfg.list_display])
        return response


# ------------------------------------------------------------------- detail
class DetailPage(ModelView):
    permission_action = "view"

    def get(self, request, app_label, model_name, pk):
        cfg = self.cfg
        obj = get_object_or_404(cfg.model._default_manager, pk=pk)

        fields = []
        for field in cfg.model._meta.concrete_fields:
            if field.name == "id":
                continue
            fields.append({"label": label_for(cfg.model, field.name), "value": display(obj, field.name)})
        for field in cfg.model._meta.many_to_many:
            fields.append({"label": label_for(cfg.model, field.name), "value": display(obj, field.name)})

        stats = []
        for prop in STAT_PROPERTIES:
            if isinstance(getattr(cfg.model, prop, None), property):
                stats.append({"label": label_for(cfg.model, prop), "value": display(obj, prop)})

        tables = []
        for spec in cfg.inlines:
            names = [
                f.name for f in spec.model._meta.concrete_fields
                if f.name not in HIDDEN_INLINE_FIELDS and f.name != spec.fk_name
            ]
            names += [p for p in INLINE_EXTRA_PROPERTIES if hasattr(spec.model, p)]
            fk_names = _fk_names(spec.model, names)
            qs = spec.model._default_manager.filter(**{spec.fk_name: obj})
            if fk_names:
                qs = qs.select_related(*fk_names)
            tables.append({
                "label": spec.label,
                "headers": [label_for(spec.model, n) for n in names],
                "rows": [[display(o, n) for n in names] for o in qs.order_by("pk")],
            })

        status = display(obj, "status") if cfg.field("status") is not None else None
        created = display(obj, "created_at")["text"] if cfg.field("created_at") is not None else ""
        updated = display(obj, "updated_at")["text"] if cfg.field("updated_at") is not None else ""

        context = self.base_context(
            obj=obj,
            title=str(obj),
            status=status,
            created=created,
            updated=updated,
            fields=fields,
            stats=stats,
            tables=tables,
            edit_url=cfg.update_url(obj.pk),
            delete_url=cfg.delete_url(obj.pk),
        )
        return render(request, "ui/detail.html", context)


def _fk_names(model, names):
    result = []
    for name in names:
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            continue
        if isinstance(field, models.ForeignKey):
            result.append(name)
    return result


# -------------------------------------------------------------- create / edit
class FormPage(ModelView):
    obj = None

    def build(self, data=None, files=None):
        cfg = self.cfg
        form_class = modelform_factory(cfg.model, form=StyledModelForm, fields="__all__")
        form = form_class(data, files, instance=self.obj)
        parent = self.obj if self.obj is not None else cfg.model()
        formsets = []
        for spec in cfg.inlines:
            formset_class = inlineformset_factory(
                cfg.model, spec.model, form=StyledModelForm, fields="__all__",
                fk_name=spec.fk_name, extra=spec.extra if self.obj is None else 0, can_delete=True,
            )
            formsets.append({"spec": spec, "formset": formset_class(data, files, instance=parent)})
        return form, formsets

    def render_form(self, request, form, formsets):
        cfg = self.cfg
        creating = self.obj is None
        context = self.base_context(
            form=form,
            formsets=formsets,
            obj=self.obj,
            creating=creating,
            title=f"New {cfg.verbose_name}" if creating else f"Edit {self.obj}",
            cancel_url=cfg.list_url if creating else cfg.detail_url(self.obj.pk),
            multipart=form.is_multipart(),
        )
        return render(request, "ui/form.html", context)

    def get(self, request, *args, **kwargs):
        form, formsets = self.build()
        return self.render_form(request, form, formsets)

    def post(self, request, *args, **kwargs):
        form, formsets = self.build(request.POST, request.FILES)
        results = [form.is_valid()] + [item["formset"].is_valid() for item in formsets]
        if all(results):
            try:
                with transaction.atomic():
                    saved = form.save()
                    for item in formsets:
                        item["formset"].instance = saved
                        item["formset"].save()
            except IntegrityError:
                messages.error(request, "Could not save — a record with the same unique value already exists.")
            else:
                messages.success(request, f"{self.cfg.verbose_name.capitalize()} “{saved}” saved.")
                return redirect(self.cfg.detail_url(saved.pk))
        else:
            messages.error(request, "Please correct the highlighted errors and try again.")
        return self.render_form(request, form, formsets)


class CreatePage(FormPage):
    permission_action = "add"


class UpdatePage(FormPage):
    permission_action = "change"

    def get(self, request, app_label, model_name, pk):
        self.obj = get_object_or_404(self.cfg.model._default_manager, pk=pk)
        return super().get(request)

    def post(self, request, app_label, model_name, pk):
        self.obj = get_object_or_404(self.cfg.model._default_manager, pk=pk)
        return super().post(request)


# ------------------------------------------------------------------- delete
class DeletePage(ModelView):
    permission_action = "delete"

    def get(self, request, app_label, model_name, pk):
        obj = get_object_or_404(self.cfg.model._default_manager, pk=pk)
        context = self.base_context(obj=obj, title=f"Delete {obj}", cancel_url=self.cfg.detail_url(obj.pk))
        return render(request, "ui/confirm_delete.html", context)

    def post(self, request, app_label, model_name, pk):
        cfg = self.cfg
        obj = get_object_or_404(cfg.model._default_manager, pk=pk)
        name = str(obj)
        try:
            obj.delete()
        except (ProtectedError, RestrictedError):
            messages.error(request, f"“{name}” cannot be deleted because other records still depend on it.")
            return redirect(cfg.detail_url(pk))
        messages.success(request, f"{cfg.verbose_name.capitalize()} “{name}” deleted.")
        return redirect(cfg.list_url)
