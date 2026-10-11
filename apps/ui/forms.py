from django import forms


def style_fields(form):
    """Give every widget Bootstrap classes and native HTML5 date/time inputs."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.HiddenInput):
            continue
        if isinstance(widget, forms.CheckboxInput):
            css = "form-check-input"
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            css = "form-select"
        else:
            css = "form-control"
        widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()

        if isinstance(field, forms.DateTimeField):
            widget.input_type = "datetime-local"
            widget.format = "%Y-%m-%dT%H:%M"
        elif isinstance(field, forms.DateField):
            widget.input_type = "date"
            widget.format = "%Y-%m-%d"
        elif isinstance(field, forms.TimeField):
            widget.input_type = "time"
            widget.format = "%H:%M"
        elif isinstance(widget, forms.Textarea):
            widget.attrs.setdefault("rows", 3)

        wide = isinstance(widget, (forms.Textarea, forms.SelectMultiple))
        field.col_class = "col-12" if wide else "col-md-6"


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            field = self.fields.get(name)
            if field is not None:
                css = field.widget.attrs.get("class", "")
                if "is-invalid" not in css:
                    field.widget.attrs["class"] = f"{css} is-invalid".strip()
