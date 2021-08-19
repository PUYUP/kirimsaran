import uuid
from datetime import date, datetime

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.files.base import File
from django.core.validators import RegexValidator
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe


class AbstractAttribute(models.Model):
    class Types(models.TextChoices):
        TEXT = "text", _("Text")
        INTEGER = "integer", _("Integer")
        BOOLEAN = "boolean", _("True / False")
        FLOAT = "float", _("Float")
        RICHTEXT = "richtext", _("Rich Text")
        DATE = "date", _("Date")
        DATETIME = "datetime", _("Datetime")
        FILE = "file", _("File")
        IMAGE = "image", _("Image")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    label = models.CharField(max_length=128)
    identifier = models.CharField(
        max_length=128,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z_]*$',
                message=_("Can only contain the letters a-z and underscores."),
                code='invalid_identifier'
            ),
        ]
    )

    type = models.CharField(
        choices=Types.choices,
        default=Types.TEXT,
        max_length=20
    )
    required = models.BooleanField(_('Required'), default=False)

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _("Attribute")
        verbose_name_plural = _("Attributes")

    @property
    def is_file(self):
        return self.type in [self.FILE, self.IMAGE]

    def __str__(self):
        return self.label

    def clean(self):
        if self.type == self.Types.BOOLEAN and self.required:
            raise ValidationError(
                _("Boolean attribute should not be required.")
            )

    def _save_file(self, value_obj, value):
        # File fields in Django are treated differently, see
        # django.db.models.fields.FileField and method save_form_data
        if value is None:
            # No change
            return
        elif value is False:
            # Delete file
            value_obj.delete()
        else:
            # New uploaded file
            value_obj.value = value
            value_obj.save()

    def _save_value(self, value_obj, value):
        if value is None or value == '':
            value_obj.delete()
            return
        if value != value_obj.value:
            value_obj.value = value
            value_obj.save()

    def save_value(self, user, value):   # noqa: C901 too complex
        AttributeValue = apps.get_model('person', 'AttributeValue')
        try:
            value_obj = user.attribute_values.get(attribute=self)
        except AttributeValue.DoesNotExist:
            # FileField uses False for announcing deletion of the file
            # not creating a new value
            delete_file = self.is_file and value is False
            if value is None or value == '' or delete_file:
                return
            value_obj = AttributeValue.objects \
                .create(user=user, attribute=self)

        if self.is_file:
            self._save_file(value_obj, value)
        else:
            self._save_value(value_obj, value)

    def validate_value(self, value):
        validator = getattr(self, '_validate_%s' % self.type)
        validator(value)

    # Validators

    def _validate_text(self, value):
        if not isinstance(value, str):
            raise ValidationError(_("Must be str"))
    _validate_richtext = _validate_text

    def _validate_float(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(_("Must be a float"))

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_("Must be a date or datetime"))

    def _validate_datetime(self, value):
        if not isinstance(value, datetime):
            raise ValidationError(_("Must be a datetime"))

    def _validate_boolean(self, value):
        if not type(value) == bool:
            raise ValidationError(_("Must be a boolean"))

    def _validate_file(self, value):
        if value and not isinstance(value, File):
            raise ValidationError(_("Must be a file field"))
    _validate_image = _validate_file


class AbstractAttributeValue(models.Model):
    """
    The "through" model for the m2m relationship between :py:class:`User <.AbstractUser>` and
    :py:class:`Attribute <.AbstractAttribute>`  This specifies the value of the attribute for
    a particular user
    For example: ``number_of_pages = 295``
    """
    attribute = models.ForeignKey('person.Attribute', on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attribute_values'
    )

    value_text = models.TextField(_('Text'), blank=True, null=True)
    value_integer = models.IntegerField(
        _('Integer'),
        blank=True,
        null=True,
        db_index=True
    )
    value_boolean = models.BooleanField(
        _('Boolean'),
        blank=True,
        null=True,
        db_index=True
    )
    value_float = models.FloatField(
        _('Float'),
        blank=True,
        null=True,
        db_index=True
    )
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(
        _('Date'),
        blank=True,
        null=True,
        db_index=True)
    value_datetime = models.DateTimeField(
        _('DateTime'),
        blank=True,
        null=True,
        db_index=True
    )
    value_file = models.FileField(
        upload_to='person/attribute/file',
        max_length=255,
        blank=True,
        null=True
    )
    value_image = models.ImageField(
        upload_to='person/attribute/image',
        max_length=255,
        blank=True,
        null=True
    )

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.attribute.type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_name = 'value_%s' % self.attribute.type

        setattr(self, attr_name, new_value)
        return

    value = property(_get_value, _set_value)

    class Meta:
        abstract = True
        app_label = 'person'
        unique_together = ('attribute', 'user')
        verbose_name = _('Attribute Value')
        verbose_name_plural = _('Attribute Values')

    def __str__(self):
        return self.summary()

    def summary(self):
        """
        Gets a string representation of both the attribute and it's value,
        used e.g in user summaries.
        """
        return "%s: %s" % (self.attribute.name, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_text property and
        return something appropriate.
        """
        property_name = '_%s_as_text' % self.attribute.type
        return getattr(self, property_name, self.value)

    @property
    def _richtext_as_text(self):
        return strip_tags(self.value)

    @property
    def value_as_html(self):
        """
        Returns a HTML representation of the attribute's value. To customise
        e.g. image attribute values, declare a ``_image_as_html`` property and
        return e.g. an ``<img>`` tag.  Defaults to the ``_as_text``
        representation.
        """
        property_name = '_%s_as_html' % self.attribute.type
        return getattr(self, property_name, self.value_as_text)

    @property
    def _richtext_as_html(self):
        return mark_safe(self.value)
