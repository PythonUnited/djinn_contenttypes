from django.db import models
from django.core.cache import cache
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

    @staticmethod
    def get_name_by_slug(slug):

        cache_key = f"content_category_{slug}"
        category_name = cache.get(cache_key)

        if not category_name:
            try:
                category_name = Category.objects.get(slug=slug).name
            except:
                category_name = slug
            if category_name == "-1":
                category_name = _("Overig")
            cache.set(cache_key, category_name)
        return category_name

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
        verbose_name=_("Category"),
        related_name='%(class)s_category',
        help_text=_("De categorie waaronder dit content-item verschijnt")
    )

    class Meta:
        abstract = True