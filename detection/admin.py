from django.contrib import admin

# Register your models here.
from detection.models import (
    Metric,
    StatisticMetric,
    Rule
)


admin.site.register(Metric)
admin.site.register(StatisticMetric)
admin.site.register(Rule)

# @admin.register(Rule)
# class RuleAdmin(admin.ModelAdmin):
#     """ Rule Admin
#     """

#     fields = (
#         'tag',
#         'instance',
#         'instance_type',
#         'cmdb_id',
#         'period',
#         'alert_level',
#         'values'
#         )