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
        queryset=CustomUser.objects.all(),
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
