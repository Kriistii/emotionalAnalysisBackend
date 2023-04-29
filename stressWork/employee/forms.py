from django import forms

class EmployeeForm(forms.Form):
    age = forms.IntegerField(min_value=18, max_value=80)
    education = forms.CharField()
    faculty = forms.CharField()
    gender = forms.ChoiceField(choices=[('M', 'Maschio'), ('F', 'Femmina'), ('O', 'Altro')])
