from django.contrib import admin
from .models import InspectionPlan, InspectionParameter, Inspection, InspectionResult, NCR, CAPA


class InspectionParameterInline(admin.TabularInline):
    model = InspectionParameter
    extra = 1


@admin.register(InspectionPlan)
class InspectionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "stage")
    list_filter = ("stage",)
    search_fields = ("name", "product__code")
    inlines = [InspectionParameterInline]


class InspectionResultInline(admin.TabularInline):
    model = InspectionResult
    extra = 1


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ("number", "stage", "product", "reference", "inspected_quantity",
                     "accepted_quantity", "rejected_quantity", "result", "inspection_date")
    list_filter = ("stage", "result")
    search_fields = ("number", "product__code", "reference")
    inlines = [InspectionResultInline]


@admin.register(NCR)
class NCRAdmin(admin.ModelAdmin):
    list_display = ("number", "product", "quantity", "status", "action_taken", "raised_date", "responsible_person")
    list_filter = ("status", "action_taken")
    search_fields = ("number", "product__code")


@admin.register(CAPA)
class CAPAAdmin(admin.ModelAdmin):
    list_display = ("number", "ncr", "responsible_person", "target_date", "status")
    list_filter = ("status",)
    search_fields = ("number", "ncr__number")
