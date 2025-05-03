from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    )
    
   

    email = models.EmailField(unique=True)  
    first_name = models.CharField(max_length=20, blank=False)
    last_name = models.CharField(max_length=20, blank=False)
    mobile = models.CharField(max_length=15, blank=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    
   
    
    REQUIRED_FIELDS = ['first_name', 'last_name', 'mobile', 'role']  

    def __str__(self):
        return self.email

    
class Skill(models.Model):
    skillname = models.CharField(max_length=100, unique=True)

    def __str__(self):
           return self.skillname
    
class Role(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    skills = models.ManyToManyField(Skill, related_name="users")
    experience = models.PositiveIntegerField(default=0)  # years of experience
    availability = models.BooleanField(default=True)
    bio = models.TextField(max_length=500, blank=True)
    preferred_roles = models.ManyToManyField(Role, related_name="users", blank=True)
    
    # ➡️ New fields
    current_load = models.PositiveIntegerField(default=0)  # Number of active projects or tasks
    LEVEL_CHOICES = [
        ('junior', 'Junior'),
        ('mid', 'Mid-Level'),
        ('senior', 'Senior'),
    ]
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='junior')

    def __str__(self):
        return self.user.username

class AddProject(models.Model):
    projectname = models.CharField(max_length=255, unique=True)
    projectdesc = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_projects")
    team_members = models.ManyToManyField(CustomUser, related_name="projects", blank=True)
    req_skills = models.ManyToManyField(Skill, related_name="projects")  # AI will use this field

    def __str__(self):
        return self.projectname

    


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('due', 'Due')
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    project = models.ForeignKey('AddProject', on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name="tasks", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.IntegerField(default=1)
    deadline = models.DateField()
    estimated_time = models.DecimalField(max_digits=5, decimal_places=2)
    required_skills = models.ManyToManyField('Skill', related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk is not None:  
            old = Task.objects.get(pk=self.pk)
            if old.status != self.status:
                self.updated_at = timezone.now()  
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title




class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.task.title}"

class TimeLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_logs")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2)
    date_logged = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.task.title} ({self.hours_spent} hrs)"
