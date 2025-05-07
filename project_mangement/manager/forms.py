from django import forms
from .models import CustomUser,UserProfile,Task,Skill,AddProject,Role
from django.core.validators import RegexValidator


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    mobile = forms.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\d{10,15}$', 'Enter a valid mobile number (10 to 15 digits).')]
    )
    class Meta:

        model = CustomUser

        fields = ['first_name', 'last_name', 'email', 'mobile', 'role', 'password']


    def clean_password(self):

        password = self.cleaned_data.get("password")

        if len(password) < 8:  # Example: enforce a minimum password length

            raise forms.ValidationError("Password must be at least 8 characters long.")

        return password


    def clean_confirm_password(self):

        password = self.cleaned_data.get("password")

        confirm_password = self.cleaned_data.get("confirm_password")


        if password != confirm_password:

            raise forms.ValidationError("Both passwords must match.")


        return confirm_password


class LoginForm(forms.Form):
    email=forms.EmailField(label="Email")
    password=forms.CharField(label="Password",widget=forms.PasswordInput())


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['skills', 'experience', 'availability', 'bio', 'preferred_roles']
        widgets = {
            'skills': forms.CheckboxSelectMultiple(),
            'preferred_roles': forms.CheckboxSelectMultiple(),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write about yourself...'}),
        }
        
      
from django.core.exceptions import ValidationError

from django import forms
from django.core.exceptions import ValidationError
from .models import AddProject, CustomUser, Skill

class AddProjectForm(forms.ModelForm):
    req_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=True,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',
            'id': 'id_req_skills',
            'data-placeholder': 'Select required skills'
        })
    )

    team_members = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),  # Will be overridden in __init__
        required=True,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2',
            'id': 'id_team_members',
            'data-placeholder': 'Select team members'
        })
    )

    class Meta:
        model = AddProject
        fields = ['projectname', 'projectdesc', 'start_date', 'end_date', 'req_skills', 'team_members']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(AddProjectForm, self).__init__(*args, **kwargs)

        # Filter users to only employees and managers
        self.fields['team_members'].queryset = CustomUser.objects.filter(role__in=['employee', 'manager'])

        # Show username with role in label
        self.fields['team_members'].label_from_instance = lambda obj: f"{obj.username} ({obj.role.capitalize()})"

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise ValidationError("End date cannot be earlier than start date.")



class AddSkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['skillname']
    def clean_skillname(self):
        skillname = self.cleaned_data['skillname']
        if Skill.objects.filter(skillname=skillname).exists():
            raise forms.ValidationError("This skill already exists.")
        return skillname
    
class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter role name'}),
        }



class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'status',
            'priority', 'deadline', 'estimated_time', 'required_skills'
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'required_skills': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
      cleaned_data = super().clean()
      deadline = cleaned_data.get("deadline")
      assigned_project = cleaned_data.get("project")  # Ensure that the project field is correctly referred to.

      if assigned_project and deadline:
        project_end_date = assigned_project.end_date  # Ensure your AddProject model has an 'end_date' field.
        if deadline > project_end_date:
            raise ValidationError("Task deadline cannot be later than the project's deadline.")
    
      return cleaned_data

    
                
from django import forms
from .models import Comment, TimeLog

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

class TimeLogForm(forms.ModelForm):
    class Meta:
        model = TimeLog
        fields = ['hours_spent']


class RecommendationForm(forms.Form):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Required Skills"
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Start Date"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="End Date"
    )
    num_people_required = forms.IntegerField(
        min_value=1,
        label="Number of People Needed"
    )
    difficulty_level = forms.ChoiceField(
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard')
        ],
        label="Difficulty Level"
    )
    preferred_role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        label="Preferred Role (Optional)"
    )
