from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):

    name = models.CharField(
        _('Category name'),
        max_length=255,
        help_text=_("Zichtbare naam van deze categorie.")
    )

    slug = models.SlugField(
        unique=True,
        help_text=_(
            "Vast kenmerk van deze categorie. Na initieel aanmaken liefst niet meer aanpassen.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Contentcategorie")
        verbose_name_plural = _("Contentcategorieën")


class CategoryMixin(models.Model):

    category = models.ForeignKey(
        Category,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_category',
        help_text=_("De categorie waaronder dit content-item verschijnt")
    )

    class Meta:
        abstract = True