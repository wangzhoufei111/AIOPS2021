# Generated by Django 2.0.4 on 2021-02-27 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('detection', '0003_auto_20210226_1801'),
    ]

    operations = [
        migrations.AddField(
            model_name='statisticmetric',
            name='is_valid',
            field=models.BooleanField(default=True, verbose_name='是否是有效告警规则'),
        ),
    ]
