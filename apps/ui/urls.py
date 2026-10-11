from django.urls import path

from . import views

app_name = "ui"

urlpatterns = [
    path("<slug:app_label>/<slug:model_name>/", views.ListPage.as_view(), name="list"),
    path("<slug:app_label>/<slug:model_name>/new/", views.CreatePage.as_view(), name="create"),
    path("<slug:app_label>/<slug:model_name>/<int:pk>/", views.DetailPage.as_view(), name="detail"),
    path("<slug:app_label>/<slug:model_name>/<int:pk>/edit/", views.UpdatePage.as_view(), name="update"),
    path("<slug:app_label>/<slug:model_name>/<int:pk>/delete/", views.DeletePage.as_view(), name="delete"),
]
