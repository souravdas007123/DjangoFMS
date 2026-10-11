"""
Registry of every model that gets a screen in the FactoryOS UI.

The list/search/filter/inline configuration is read from the existing
``admin.py`` files, so a model registered there automatically appears in the
new interface (list, create, edit, detail, delete) without extra code.
"""
from dataclasses import dataclass
from functools import lru_cache

from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import Http404
from django.urls import reverse
from django.utils.text import capfirst

# (app_label, sidebar label, Font Awesome icon)
GROUPS = (
    ("masters", "Masters", "fa-boxes-stacked"),
    ("sales", "Sales", "fa-cart-shopping"),
    ("purchase", "Procurement", "fa-file-contract"),
    ("inventory", "Inventory", "fa-warehouse"),
    ("production", "Production", "fa-industry"),
    ("quality", "Quality", "fa-clipboard-check"),
    ("maintenance", "Maintenance", "fa-wrench"),
    ("hr", "Workforce", "fa-users"),
    ("dispatch", "Dispatch", "fa-truck-fast"),
    ("costing", "Costing", "fa-rupee-sign"),
)
GROUP_LABELS = {key: label for key, label, _icon in GROUPS}
GROUP_ICONS = {key: icon for key, _label, icon in GROUPS}


@dataclass(frozen=True)
class FilterSpec:
    name: str
    label: str
    kind: str  # "choices" | "bool" | "fk"


@dataclass(frozen=True)
class InlineSpec:
    model: type
    fk_name: str
    label: str
    extra: int


@dataclass(frozen=True)
class ModelConfig:
    model: type
    group: str
    list_display: tuple
    search_fields: tuple
    filters: tuple
    inlines: tuple

    # ---- naming -------------------------------------------------------
    @property
    def app_label(self):
        return self.model._meta.app_label

    @property
    def model_name(self):
        return self.model._meta.model_name

    @property
    def verbose_name(self):
        return str(self.model._meta.verbose_name)

    @property
    def verbose_name_plural(self):
        return str(self.model._meta.verbose_name_plural)

    @property
    def group_label(self):
        return GROUP_LABELS[self.group]

    @property
    def group_icon(self):
        return GROUP_ICONS[self.group]

    def perm(self, action):
        return f"{self.app_label}.{action}_{self.model_name}"

    # ---- urls ---------------------------------------------------------
    @property
    def list_url(self):
        return reverse("ui:list", args=[self.app_label, self.model_name])

    @property
    def create_url(self):
        return reverse("ui:create", args=[self.app_label, self.model_name])

    def detail_url(self, pk):
        return reverse("ui:detail", args=[self.app_label, self.model_name, pk])

    def update_url(self, pk):
        return reverse("ui:update", args=[self.app_label, self.model_name, pk])

    def delete_url(self, pk):
        return reverse("ui:delete", args=[self.app_label, self.model_name, pk])

    # ---- field helpers ------------------------------------------------
    def field(self, name):
        try:
            return self.model._meta.get_field(name)
        except FieldDoesNotExist:
            return None

    def is_fk(self, name):
        return isinstance(self.field(name), models.ForeignKey)

    def is_sortable(self, name):
        field = self.field(name)
        return field is not None and field.concrete and not field.many_to_many


def _find_fk(child, parent):
    for field in child._meta.get_fields():
        if isinstance(field, models.ForeignKey) and field.remote_field.model is parent:
            return field.name
    return None


def _build_filters(model, names):
    specs = []
    for name in names:
        if not isinstance(name, str):
            continue
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            continue
        if getattr(field, "choices", None):
            kind = "choices"
        elif isinstance(field, models.BooleanField):
            kind = "bool"
        elif isinstance(field, models.ForeignKey):
            kind = "fk"
        else:
            continue
        specs.append(FilterSpec(name=name, label=capfirst(str(field.verbose_name)), kind=kind))
    return tuple(specs)


def _build_inlines(model, model_admin):
    specs = []
    for inline in getattr(model_admin, "inlines", ()):
        fk_name = _find_fk(inline.model, model)
        if not fk_name:
            continue
        specs.append(
            InlineSpec(
                model=inline.model,
                fk_name=fk_name,
                label=capfirst(str(inline.model._meta.verbose_name_plural)),
                extra=max(int(getattr(inline, "extra", 1) or 0), 1),
            )
        )
    return tuple(specs)


@lru_cache(maxsize=1)
def get_registry():
    """Ordered mapping {(app_label, model_name): ModelConfig}."""
    configs = {}
    for model, model_admin in admin.site._registry.items():
        app_label = model._meta.app_label
        if app_label not in GROUP_LABELS:
            continue
        configs[(app_label, model._meta.model_name)] = ModelConfig(
            model=model,
            group=app_label,
            list_display=tuple(n for n in model_admin.list_display if isinstance(n, str)) or ("__str__",),
            search_fields=tuple(model_admin.search_fields or ()),
            filters=_build_filters(model, model_admin.list_filter or ()),
            inlines=_build_inlines(model, model_admin),
        )
    ordered = {}
    for key, _label, _icon in GROUPS:
        for pair, cfg in configs.items():
            if pair[0] == key:
                ordered[pair] = cfg
    return ordered


def configs_in_group(group):
    return [cfg for (app_label, _m), cfg in get_registry().items() if app_label == group]


def get_config(app_label, model_name):
    try:
        return get_registry()[(app_label, model_name)]
    except KeyError:
        raise Http404("Unknown module")
