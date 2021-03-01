from django.db import models

# Create your models here.
# Metric和StatisticMetric当成时序数据库使用
# instance + instance_type作为唯一主键


class Metric(models.Model):
    """ 存放kpi时序数据
    """

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    timestamp = models.CharField('本身时间戳10位(对应created_time)', max_length=256, null=True)

    instance = models.CharField('指标名称', max_length=256, null=True)
    instance_type = models.CharField('指标类型', max_length=256, null=True)

    value = models.DecimalField('真实值value', max_digits=20, decimal_places=1, null=True)
    mu = models.DecimalField('基线mu', max_digits=20, decimal_places=1, null=True)
    n_lower = models.DecimalField('n_lower', max_digits=20, decimal_places=1, null=True)
    n_upper = models.DecimalField('n_upper', max_digits=20, decimal_places=1, null=True)
    std = models.DecimalField('std', max_digits=20, decimal_places=1, null=True)

    status = models.CharField('异常或正常status', max_length=256, null=True)
    is_outiler= models.BooleanField('是否超过阈值', default=False)
    is_alert = models.BooleanField('是否告警', default=False)
    during = models.CharField('告警持续时间', max_length=256, null=True)
    alert_id = models.CharField('alert_id', max_length=256, null=True)

    class Meta:
        indexes = [
            models.Index(fields = ['timestamp'],name = 'metric_timestamp_index'),
            models.Index(fields = ['instance'],name = 'metric_instance_index'),
            models.Index(fields = ['instance_type'],name = 'metric_instance_type_index')
        ]


class StatisticMetric(models.Model):
    """ 存放kpi时序的统计量
    """

    created_time = models.DateTimeField('创建时间', auto_now_add=True)

    is_valid = models.BooleanField('是否是有效告警规则', default=True)
    instance = models.CharField('指标名称', max_length=256, null=True)
    instance_type = models.CharField('指标类型', max_length=256, null=True)

    n_lower = models.DecimalField('n_lower', max_digits=20, decimal_places=1, null=True)
    n_upper = models.DecimalField('n_upper', max_digits=20, decimal_places=1, null=True)
    std = models.CharField('std', max_length=256, null=True)

    class Meta:
        indexes = [
            models.Index(fields = ['instance'],name = 'statistic_instance_index'),
            models.Index(fields = ['instance_type'],name = 'statistic_instance_type_index')
        ]


class Rule(models.Model):
    """ Rule存放告警规则
    """

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    updated_time = models.DateTimeField('更新时间', auto_now=True)

    is_valid = models.BooleanField('是否是有效告警规则', default=True)
    tag = models.CharField('tag(业务/性能/日志)', max_length=256, null=True)
    instance = models.CharField('指标名称', max_length=256, null=True)
    instance_type = models.CharField('指标类型', max_length=256, null=True)
    cmdb_id = models.CharField('cmdb_id', max_length=256, null=True)

    period =  models.IntegerField('指标采样周期', default=60)
    alert_level = models.CharField('alert_level', max_length=256, null=True)
    values = models.CharField('告警配置参数', max_length=256, null=True)

    class Meta:
        indexes = [
            models.Index(fields = ['instance'],name = 'rule_instance_index'),
            models.Index(fields = ['instance_type'],name = 'rule_instance_type_index')
        ]


class RiskEvent(models.Model):
    """ 风险事件
    """

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    updated_time = models.DateTimeField('更新时间', auto_now=True)

    tag = models.CharField('tag(业务/性能/日志)', max_length=256, null=True)
    instance = models.CharField('指标名称', max_length=256, null=True)
    instance_type = models.CharField('指标类型', max_length=256, null=True)
    cmdb_id = models.CharField('cmdb_id', max_length=256, null=True)

    alert_id = models.CharField('alert_id', max_length=256, null=True)
    reason = models.TextField('告警原因', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields = ['instance'],name = 'risk_instance_index'),
            models.Index(fields = ['instance_type'],name = 'risk_instance_type_index')
        ]
