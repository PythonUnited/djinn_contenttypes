# Generated by Django 2.0.13 on 2021-11-22 21:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djinn_contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Zichtbare naam van deze categorie.', max_length=255, verbose_name='Category name')),
                ('slug', models.SlugField(help_text='Vast kenmerk van deze categorie. Na initieel aanmaken liefst niet meer aanpassen.', unique=True)),
            ],
            options={
                'verbose_name': 'Contentcategorie',
                'verbose_name_plural': 'Contentcategorieën',
            },
        ),
    ]
