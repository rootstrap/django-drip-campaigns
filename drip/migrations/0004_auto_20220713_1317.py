# Generated by Django 3.2.14 on 2022-07-13 13:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('drip', '0003_testuseruuidmodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('delete_drips', models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name='drip',
            name='campaign',
            field=models.ForeignKey(blank=True, default=None, help_text='If set, this is the campaign to which this Drip belongs to.', null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='drip.campaign'),
        ),
    ]
