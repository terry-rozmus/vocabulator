from django import forms

class SearchForm(forms.Form):
    sentence = forms.CharField()
