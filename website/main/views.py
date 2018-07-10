import logging
import sys
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
from .forms import SearchForm
from .frequency import *
from .models import School, Grade, Book, Unit, Bookmark, Word

from .config import *

def get_form_data(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        form = SearchForm(request.POST)

        # Check whether the form is valid.
        if form.is_valid():
            # Convert data format so it is suitable for use in the template
            form_data_in = dict(request.POST)
            sentence = form_data_in['sentence'][0]
            checkboxes_checked = [int(str(key)[5:])
                                  for key, value
                                  in form_data_in.items()
                                  if key[0:5] == 'bkmk_']

            # Errors and warnings
            if checkboxes_checked == []:
                error = 'You need to choose some books, lessons or units on ' \
                        'the left of the screen.'
            else:
                error = ''

            form_data_out = {'sentence': sentence,
                             'checked': checkboxes_checked,
                             'error': error}

            return form_data_out
    return {'sentence': '', 'checked': [], 'error': ''}


def get_warning_colour(frequency):
    # Make frequency group levels
    common_level = common_word_frequency
    less_common = common_level / 2

    # Set warning colours.
    if frequency < less_common:
        red = format(int((1 - (frequency / less_common)) * 255), '02X')
        blue = format(int(frequency / less_common * 255), '02X')
    elif frequency < common_level:
        red = '00'
        blue = format(int((1 - (frequency - less_common) / less_common)
               * 255), '02X')
    if frequency >= common_level:
        warning = 0
    else:
        warning = red + '00' + blue

    return warning


def get_words(sentence, checked):
    words = list()
    if sentence != '' and checked != []:
        word_count_cache = {}

        sentence_words = re.split("[^a-z'\-]+", sentence.lower().strip())
        sentence_words = list(filter(None, sentence_words))

        # Get the total word count from the Words table
        total_count = 0
        for index, checkbox in enumerate(checked):
            try:
                total_count += Word.objects \
                    .filter(bookmark_id=checkbox) \
                    .aggregate(Sum('count'))['count__sum']
            except:
                # Log the bookmark that has no words and then delete so it
                # can't be used in further analysis
                logging.warning('No words in this bookmark: ' + str(checkbox))
                del(checked[index])

        # Get the word frequency for each word in the sentence.
        for word in sentence_words:
            if word not in word_count_cache.keys():
                # Get the count of the current word from the Words DB table
                word_count = 0
                for checkbox in checked:
                    bookmark_word_count = Word.objects \
                        .filter(bookmark_id=checkbox) \
                        .filter(word__exact=word) \
                        .aggregate(Sum('count'))['count__sum']
                    if bookmark_word_count is not None:
                        word_count += bookmark_word_count
                word_count_cache[word] = word_count
            else:
                # Get the count from the temporary words cache
                word_count = word_count_cache[word]

            # Calculate the frequency.
            frequency = float(word_count) / float(total_count)
            print (frequency)

            # Get warning colour
            warning = get_warning_colour(frequency)

            # Make the words list.
            words += [{'word': word,
                       'count': word_count,
                       'frequency': round(frequency * 100, 4),
                       'warning': warning}]
    return words


def get_key_colours():
    categories = list()

    # Get the level at which words are considered 'common'
    common_level = common_word_frequency

    # Get interval size
    interval = common_level / 8

    # Make catregory names
    names = ['Common (>' + str(round(common_level * 100, 4)) + '%),',
             'Common,',
             'Quite',
             'Common,',
             'Less',
             'Common,',
             'Rare,',
             'Few,',
             'or None (0%)'
             ]

    for i in range(9):
        # Get category warning colours
        frequency = common_level - i * interval
        warning = get_warning_colour(frequency)

        # Make the key list.
        categories += [{'name': names[i], 'warning': warning}]

    return categories


def set_cookie(response, form_data):
    response.set_cookie('Checked_Items', form_data, max_age=365*24*60*60*10)
    return response


def get_cookie(request):
    checked_items_in = request.COOKIES.get('Checked_Items', None)
    if checked_items_in is not None:
        checked_items_in = eval(checked_items_in)
        checked_items_out = [int(str(item)) for item in checked_items_in]
        return checked_items_out
    else:
        return []


def index(request):
    # Prepare the data for the menu tree
    # tree = dict()
    tree = list()
    grade_branch = list()
    book_branch = list()
    unit_branch = list()
    book_type = ContentType.objects.get(app_label="main", model="book")
    unit_type = ContentType.objects.get(app_label="main", model="unit")
    # Prepare the books data structure
    schools = School.objects.order_by('order')
    for school in schools:
        grades = Grade.objects.filter(school_id=school.id).order_by('order')
        for grade in grades:
            books = Book.objects.filter(grade_id=grade.id)
            for book in books:
                units = Unit.objects.filter(book_id=book.id)
                for unit in units:
                    bookmarks = Bookmark.objects\
                                        .filter(parent_id=unit.id) \
                                        .filter(parent_type_id=unit_type.id) \
                                        .order_by('order')
                    unit_branch.append([str(unit.unit_title), bookmarks])
                bookmarks = Bookmark.objects \
                                    .filter(parent_id=book.id) \
                                    .filter(parent_type_id=book_type.id)
                book_branch.append(
                        [str(book.book_title), unit_branch + list(bookmarks)]
                )
                unit_branch = list()  # Clear book branch dict ready
                                      # for next branch
            grade_branch.append([str(grade.grade_level), book_branch])
            book_branch = list()  # Clear book branch dict ready
                                  # for next branch
        tree.append([str(school.school_type), grade_branch])
        # tree[str(school.school_type)] = grade_branch
        sys.stdout.write(str(tree))
        grade_branch = list()  # Clear grade branch dict ready for next branch

    # Process sentence into words
    form_data = get_form_data(request)
    sentence = form_data['sentence']
    checked_items = form_data['checked']
    words = get_words(sentence, checked_items)

    # Make response object and set or get the checked items cookie before
    # returning
    if checked_items == []:  # if not a form post, use the cookie instead
        form_data['checked'] = get_cookie(request)
    response = render(request, 'main/index.html', {
        'form_data': form_data,
        'sentence': sentence,
        'words': words,
        'error': form_data['error'],
        'tree': tree,
    })
    if checked_items != []:  # If it is a form post, set the cookie
        response = set_cookie(response, checked_items)
    #print(form_data['checked'])
    #for item in form_data['checked']:
    #    print(type(item))
    return response


def results(request):
    # Process sentence into words
    form_data = get_form_data(request)
    sentence = form_data['sentence']
    words = get_words(sentence, form_data['checked'])
    categories = get_key_colours()

    # Make response object and set the checked items cookie before returning
    response = render(request, 'main/results.html', {
        'words': words,
        'categories': categories,
        'error': form_data['error'],
    })
    response = set_cookie(response, form_data['checked'])
    return response


