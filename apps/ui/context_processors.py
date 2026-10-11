from django.utils.text import capfirst

from . import registry


def navigation(request):
    """Sidebar groups, limited to the models the signed-in user may view."""
    user = getattr(request, "user", None)
    match = getattr(request, "resolver_match", None)
    if user is None or not user.is_authenticated or match is None:
        return {}
    if match.namespace not in ("ui", "dashboard"):
        return {}

    current = (match.kwargs.get("app_label"), match.kwargs.get("model_name"))
    groups = []
    for key, label, icon in registry.GROUPS:
        items = []
        for cfg in registry.configs_in_group(key):
            if not user.has_perm(cfg.perm("view")):
                continue
            items.append({
                "label": capfirst(cfg.verbose_name_plural),
                "url": cfg.list_url,
                "active": (cfg.app_label, cfg.model_name) == current,
            })
        if items:
            groups.append({
                "key": key, "label": label, "icon": icon, "items": items,
                "open": any(item["active"] for item in items),
            })
    return {"ui_nav": groups}
