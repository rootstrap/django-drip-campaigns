# Generated by Django 3.2.14 on 2022-07-29 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drip', '0004_auto_20220713_1317'),
    ]

    operations = [
        migrations.AlterField(
            model_name='querysetrule',
            name='lookup_type',
            field=models.CharField(choices=[('exact', 'exactly'), ('iexact', 'exactly (case insensitive)'), ('contains', 'contains'), ('icontains', 'contains (case insensitive)'), ('regex', 'regex'), ('iregex', 'regex (case insensitive)'), ('gt', 'greater than'), ('gte', 'greater than or equal to'), ('lt', 'less than'), ('lte', 'less than or equal to'), ('startswith', 'starts with'), ('endswith', 'ends with'), ('istartswith', 'starts with (case insensitive)'), ('iendswith', 'ends with (case insensitive)')], default='exact', max_length=12),
        ),
    ]
