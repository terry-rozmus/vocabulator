from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class TinyIntegerField(models.SmallIntegerField):
    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return "tinyint"
        else:
            return super(TinyIntegerField, self).db_type(connection)


class PositiveTinyIntegerField(models.PositiveSmallIntegerField):
    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return "tinyint unsigned"
        else:
            return super(PositiveTinyIntegerField, self).db_type(connection)


class School(models.Model):
    school_type = models.CharField(max_length=40)
    order = PositiveTinyIntegerField(default=1)

    # Make the identity of db rows clear in admin
    def __str__(self):
        return self.school_type


class Grade(models.Model):
    school = models.ForeignKey(School)
    grade_level = models.CharField(max_length=40)
    order = PositiveTinyIntegerField(default=1)

    # Make the identity of db rows clear in admin
    def __str__(self):
        return str(self.school) + ' > ' + str(self.grade_level)


class Book(models.Model):
    grade = models.ForeignKey(Grade)
    book_title = models.CharField(max_length=40)
    date_published = models.DateField('date published')

    # Make the identity of db rows clear in admin
    def __str__(self):
        return str(self.grade) + ' > ' + str(self.book_title)


class Unit(models.Model):
    book = models.ForeignKey(Book)
    unit_title = models.CharField(max_length=40)
    order = PositiveTinyIntegerField(default=1)

    # Make the identity of db rows clear in admin
    def __str__(self):
        return str(self.book) + ' > ' + str(self.unit_title)


class Bookmark(models.Model):
    # book = models.ForeignKey(Book)
    order = PositiveTinyIntegerField(default=1)
    limit = models.Q(app_label = 'main', model = 'book') | \
            models.Q(app_label = 'main', model = 'unit')
    parent_type = models.ForeignKey(
            ContentType, on_delete=models.CASCADE,
            limit_choices_to=limit,
            null=True
    )
    parent_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('parent_type', 'parent_id')
    section_title = models.CharField(max_length=60)
    content = models.TextField(default="", blank=True)
    vocabulary = models.TextField(default="", blank=True)
    # process_words = models.BooleanField()

    # Make the identity of db rows clear in admin
    def __str__(self):
        return str(self.parent_type) + ' > ' + str(self.section_title)


class Word(models.Model):
    bookmark = models.ForeignKey(Bookmark)
    word = models.CharField(max_length=20)
    count = models.IntegerField()

    # Make the identity of db rows clear in admin
    def __str__(self):
        return str(self.bookmark) + ' > ' + str(self.word)

