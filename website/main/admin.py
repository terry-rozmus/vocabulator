from django.contrib import admin
from django.forms import Textarea
from django.db import models
from django.contrib.contenttypes.models import ContentType

from .frequency import VocabularyProcess
from .models import School, Grade, Book, Unit, Bookmark, Word


# Action menu item
def process_content(modeladmin, request, queryset):
    # Get the text from the database bookmark item
    table = queryset.values_list('id', 'content', 'vocabulary')
    # Process each record in the queryset
    for record in table:
        bookmark_id = int(record[0])
        content_text = str(record[1]).lower() + str(record[2]).lower()
        # make it into a list of lines
        content_list = content_text.splitlines()
        # Process the text into a dictionary of words with counts
        vocabulary_obj = VocabularyProcess(content_list)
        words = vocabulary_obj.get_frequency_dict()
        # Update or create the words and counts in the Words table.
        for word, count in words.items():
            # Encode to utf-8 for compatibility with current DB char encoding
            word = word.encode('utf-8')
            if len(word) <= 20:  # Ensure the word will fit in the DB record
                Word.objects.update_or_create(word=word, \
                           bookmark_id=bookmark_id, defaults={'count': count})

# Make a more helpful name for the action menu item
process_content.short_description = "Process content into a word count list"


class BookmarkInline(admin.TabularInline):
    model = Bookmark
    extra = 0
    show_change_link = True
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols': 40})},
    }


class BookAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['grade', 'book_title']}),
        ('Publication Date', {'fields': ['date_published'], 'classes': ['collapse']}),
    ]
    list_display = ['book_title', 'id', 'grade']


class UnitAdmin(admin.ModelAdmin):
    list_display = ['unit_title', 'order', 'id', 'book']


class WordInline(admin.TabularInline):
    model = Word
    readonly_fields = ('word', 'count')
    extra = 0
    show_change_link = True


class BookmarkAdmin(admin.ModelAdmin):
    # fields = ['parent_type', 'parent_is', 'section_title', 'content']
    list_display = ['section_title', 'order', 'parent_type_id', 'parent_is']
    inlines = [WordInline]
    actions = [process_content]

    def parent_is(self, obj):
        # Get the id of the 'book' content type
        book_type = ContentType.objects.get(app_label="main", model="book")
        # If the object content type id is a book then find the book's title
        if obj.parent_type_id == book_type.id:
            book = Book.objects.get(id=obj.parent_id)
            return book.book_title
        # else return the unit title with the book title
        else:
            unit = Unit.objects.get(id=obj.parent_id)
            book = Book.objects.get(id=unit.book_id)
            return book.book_title + ' > ' + unit.unit_title


class WordAdmin(admin.ModelAdmin):
    readonly_fields = ('word', 'count')


admin.site.register(School)
admin.site.register(Grade)
admin.site.register(Book, BookAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(Bookmark, BookmarkAdmin)
