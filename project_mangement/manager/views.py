from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth import login, authenticate,logout
from django.contrib import messages
from .forms import AddProjectForm, CommentForm, RegistrationForm, LoginForm, RoleForm, TaskForm, TimeLogForm,UserProfileForm
from .models import AddProject, CustomUser, Role, Task,UserProfile,Skill,TimeLog
from django.db.models import Count, Sum
from django.views.decorators.cache import cache_control
from django.utils import timezone



def index(request):
    return render(request,"manager/index.html")

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            if CustomUser.objects.filter(email=email).exists():
                # Return error message in JSON format
                return JsonResponse({
                    'success': False,
                    'message': 'Email is already in use. Please choose another one.'
                })

            user_info = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
                'mobile': form.cleaned_data['mobile'],
                'role': form.cleaned_data['role'],
            }

            save_user(user_info)

            return JsonResponse({
                'success': True,
                'message': 'Account created successfully! You can now login.',
                'redirect_url': '/login/'  # Redirect to the login page
            })
        
        # If form is not valid, return error message in JSON format
        return JsonResponse({
            'success': False,
            'message': 'There was an error with your form. Please check the fields and try again.',
            'errors': form.errors
        })
    else:
        form = RegistrationForm()

    return render(request, 'manager/register.html', {'form': form})

def save_user(user_info):
    user = CustomUser(
        first_name=user_info['first_name'],
        last_name=user_info['last_name'],
        email=user_info['email'],
        username=user_info['email'],  # using email as username
        mobile=user_info['mobile'],
        role=user_info['role'],
    )
    user.set_password(user_info['password'])  # hashes the password
    user.save()
    return user


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_user(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'manager':
            return redirect('manager_dashboard')
        elif request.user.role == 'employee':
            return redirect('employee_dashboard')

    form = LoginForm()
    return render(request, 'manager/login.html', {'form': form})


def process_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)

            if user:
                login(request, user)
                role = user.role
                if role == 'admin':
                    return JsonResponse({'success': True, 'redirect_url': '/admin_dashboard/'})
                elif role == 'manager':
                    return JsonResponse({'success': True, 'redirect_url': '/manager_dashboard/'})
                elif role == 'employee':
                    return JsonResponse({'success': True, 'redirect_url': '/employee_dashboard/'})
                else:
                    return JsonResponse({'success': False, 'message': 'Unknown user role'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid email or password'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def normalize_time(total_hours_raw):
    """
    Normalizes a float total hour value into a formatted string 'Xh Ymin'.
    :param total_hours_raw: Total hours as a float (e.g., 2.7)
    :return: Formatted string in 'Xh Ymin' format (e.g., '2h 42min')
    """
    hours = int(total_hours_raw)
    minutes = round((total_hours_raw - hours) * 60)
    return f"{hours}h {minutes}min"



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def admin_dashboard(request):
    # Ensure that only users with 'admin' role can access this dashboard
    if request.user.role != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page.")

    # Analytics Data
    total_users = CustomUser.objects.count()
    total_projects = AddProject.objects.count()
    total_tasks = Task.objects.count()
    
    task_status_counts = Task.objects.values('status').annotate(count=Count('id'))
    
    # Aggregate total hours logged
    total_hours_raw = TimeLog.objects.aggregate(total_hours=Sum('hours_spent'))['total_hours'] or 0

    # Normalize time
    time_logged = normalize_time(total_hours_raw)

    context = {
        'total_users': total_users,
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'task_status_counts': task_status_counts,
        'time_logged': time_logged,
    }

    return render(request, 'manager/admin_dashboard.html', context)



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manager_dashboard(request):
    if request.user.role != 'manager':
        return HttpResponseForbidden("You are not authorized to view this page.")
    
    manager_projects = AddProject.objects.filter(created_by=request.user)
    
    print("Manager:", request.user)
    print("Projects:", list(manager_projects.values('projectname', 'created_by')))

    return render(request, 'manager/manager_dashboard.html', {
        'projects': manager_projects
    })


def compute_priority_score(task):
    days_left = (task.deadline - timezone.now().date()).days
    days_left = max(days_left, 1)
    urgency_score = (task.priority * 10) / days_left
    efficiency_bonus = max(10 - float(task.estimated_time), 0)
    return urgency_score + efficiency_bonus

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def employee_dashboard(request):
    user = request.user

    if user.role != 'employee':
        return HttpResponseForbidden("You are not authorized to view this page.")

    all_tasks = Task.objects.filter(assigned_to=user)
    tasks_todo = all_tasks.filter(status='todo')
    tasks_in_progress = all_tasks.filter(status='in_progress')
    tasks_completed = all_tasks.filter(status='completed')
    tasks_due = all_tasks.filter(status='due')

    actionable_tasks = all_tasks.filter(status__in=['todo', 'in_progress'])
    sorted_tasks = sorted(actionable_tasks, key=compute_priority_score, reverse=True)
    top_task = sorted_tasks[0] if sorted_tasks else None

    return render(request, 'manager/employee_dashboard.html', {
        'tasks_todo': tasks_todo,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
        'tasks_due': tasks_due,
        'recommended_task': top_task,
    })
 



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_logout(request):
    logout(request)
    return redirect('index')


@login_required
def profile_view(request):
    try:
        profile = request.user.profile  # OneToOne link
    except UserProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            form.save_m2m()  # Save ManyToMany fields like skills, preferred_roles
            return redirect('profile_view')  # Reload page after save
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'manager/profile.html', {'form': form})



def skill_manage(request):
    skills = Skill.objects.all()

    # Handle Add or Update
    if request.method == "POST":
        skill_id = request.POST.get('skill_id')
        skill_name = request.POST.get('skillname')

        if skill_id:  # Update existing skill
            skill = get_object_or_404(Skill, id=skill_id)
            skill.skillname = skill_name
            skill.save()
            messages.success(request, 'Skill updated successfully.')
        else:  # Add new skill
            Skill.objects.create(skillname=skill_name)
            messages.success(request, 'Skill added successfully.')

        return redirect('skill_manage')  # Redirect to the same page

    return render(request, 'manager/skill_manage.html', {
        'skills': skills,
    })

    # Handle Delete
    delete_id = request.GET.get('delete_id')
    if delete_id:
        skill = get_object_or_404(Skill, id=delete_id)
        skill.delete()
        messages.success(request, 'Skill deleted successfully.')
        return redirect('skill_manage')

    return render(request, 'manager/skill_manage.html', {'skills': skills})

def add_role(request):
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_role')  
    else:
        form = RoleForm()

    roles = Role.objects.all()
    return render(request, 'manager/add_role.html', {'form': form, 'roles': roles})


def user_list_view(request):
    users = CustomUser.objects.exclude(role='admin').select_related('profile').prefetch_related('profile__skills', 'profile__preferred_roles')
    return render(request, 'manager/users_data.html', {'users': users})

def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect('admin_home')  


def skill_delete(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id)
    skill.delete()
    messages.success(request, 'Skill deleted successfully.')
    return redirect('skill_manage')

@login_required
def add_project(request):
    if request.method == "POST":
        form = AddProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()

            # For AI logic, you can access:
            required_role = request.POST.get("required_role")
            num_people = request.POST.get("num_people_required")

            # You can use these values for suggesting team members, not saving them
            # print(required_role, num_people)

            return redirect(manager_dashboard)
        else:
            return render(request, "manager/add_project.html", {
                "form": form,
                "skills": Skill.objects.all(),
                "users": CustomUser.objects.all()
            })
    else:
        form = AddProjectForm()
        return render(request, "manager/add_project.html", {
            "form": form,
            "skills": Skill.objects.all(),
            "users": CustomUser.objects.all()
        })
        
def project_detail(request, pk):
    project = get_object_or_404(AddProject, pk=pk)
    tasks = project.tasks.all()  # Using related_name="tasks"
    return render(request, 'manager/project_detail.html', {
        'project': project,
        'tasks': tasks,
    })

def update_project(request, pk):
    project = get_object_or_404(AddProject, pk=pk)
    if request.method == 'POST':
        form = AddProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_detail', pk=project.pk)
    else:
        form = AddProjectForm(instance=project)
    return render(request, 'manager/update_project.html', {'form': form, 'project': project})

def delete_project(request, pk):
    project = get_object_or_404(AddProject, pk=pk)
    if request.method == 'POST':
        project.delete()
        return redirect('manager_dashboard')
    return render(request, 'projects/delete_project_confirm.html', {'project': project})


# manager home
def manager_home(request):
    user = request.user
    projects = AddProject.objects.filter(created_by=user)

    tasks_todo = Task.objects.filter(assigned_to=user, status='todo')
    tasks_in_progress = Task.objects.filter(assigned_to=user, status='in_progress')
    tasks_completed = Task.objects.filter(assigned_to=user, status='completed')
    tasks_due = Task.objects.filter(assigned_to=user, status='due')

    return render(request, "manager/manager_home.html", {
        'projects': projects,
        'tasks_todo': tasks_todo,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
        'tasks_due': tasks_due,
    })


def add_task(request, project_id):
    try:
        project = AddProject.objects.get(id=project_id)
    except AddProject.DoesNotExist:
        return redirect('error_page')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        form.fields['assigned_to'].queryset = project.team_members.all()  # Limit members to project team
        if form.is_valid():
            task = form.save(commit=False)  # Don't save yet
            task.project = project  # Assign project to the task
            task.save()  # Save the task
            form.save_m2m()  # Save many-to-many fields like required_skills
            return redirect('project_detail', pk=project.id)
        else:
            print(form.errors)  # For debugging

    else:
        form = TaskForm()
        form.fields['assigned_to'].queryset = project.team_members.all()  # Limit members to project team

    return render(request, 'manager/add_task.html', {
        'form': form,
        'project': project
    })


def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # --- Handle Comment Form ---
    if request.method == 'POST' and 'comment' in request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            return redirect('task_detail', task_id=task.id)
    else:
        comment_form = CommentForm()

    # --- Handle Time Log Form ---
    if request.method == 'POST' and 'time_log' in request.POST:
        time_log_form = TimeLogForm(request.POST)
        if time_log_form.is_valid():
            time_log = time_log_form.save(commit=False)
            time_log.task = task
            time_log.user = request.user
            time_log.save()
            return redirect('task_detail', task_id=task.id)
    else:
        time_log_form = TimeLogForm()

    # --- Handle Task Status Update Form (Only 'status' field) ---
    if request.method == 'POST' and 'update_status' in request.POST:
        status_form = TaskForm(request.POST, instance=task)
        # Only allow 'status' field to be updated
        status_form.fields.clear()
        status_form.fields['status'] = TaskForm(request.POST, instance=task).fields['status']
        if status_form.is_valid():
            task.status = status_form.cleaned_data['status']
            task.save()
            return redirect('task_detail', task_id=task.id)
    else:
        status_form = TaskForm(instance=task)
        # Hide all fields except status
        allowed_status_field = status_form.fields['status']
        status_form.fields.clear()
        status_form.fields['status'] = allowed_status_field

    # --- Comments and Time Logs ---
    comments = task.comments.all()
    time_logs = task.time_logs.all()

    # --- Time Calculations ---
    total_time_logged = sum(tl.hours_spent for tl in time_logs)
    time_remaining = max(task.estimated_time - total_time_logged, 0) if task.estimated_time else 0
    progress_percentage = (total_time_logged / task.estimated_time) * 100 if task.estimated_time else 0
    progress_percentage = min(progress_percentage, 100)
   
    return render(request, 'manager/task_detail.html', {
        'task': task,
        'comment_form': comment_form,
        'time_log_form': time_log_form,
        'status_form': status_form,
        'comments': comments,
        'time_logs': time_logs,
        'total_time_logged': total_time_logged, 
        'time_remaining': time_remaining, 
        'progress_percentage': progress_percentage,
    })




        

# def add_project_options(request):
#     return render(request, 'manager_pages/project_options.html')



from .forms import RecommendationForm
from .recommend import recommend_employees  # wherever your recommend_employees function is
@login_required
def recommend_project(request):
    recommendations = None

    if request.method == 'POST':
        if 'save_project' in request.POST:
            projectname = request.POST.get('projectname')
            projectdesc = request.POST.get('projectdesc')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            difficulty_level = request.POST.get('difficulty_level')  # used only for re-recommendation
            num_people_required = request.POST.get('num_people_required')
            skills = request.POST.getlist('skills')
            selected_employee_ids = request.POST.getlist('selected_employees')

            if not selected_employee_ids:
                messages.error(request, "You must select at least one employee before saving the project.")

                # Recompute recommendations to retain the selection
                recommendations = recommend_employees(
                    skills=skills,
                    start_date=start_date,
                    end_date=end_date,
                    num_people_required=int(num_people_required),
                    difficulty_level=difficulty_level,
                    preferred_role=None  # or carry over if needed
                )

                return render(request, 'manager/recommend_project.html', {
                    'form': RecommendationForm(request.POST),
                    'recommendations': recommendations,
                    'projectname': projectname,
                    'projectdesc': projectdesc,
                    'skills': skills,
                    'start_date': start_date,
                    'end_date': end_date,
                    'difficulty_level': difficulty_level,
                    'num_people_required': num_people_required
                })

            # Save project (⛔ don't save difficulty_level)
            project = AddProject.objects.create(
                projectname=projectname,
                projectdesc=projectdesc,
                start_date=start_date,
                end_date=end_date,
                created_by=request.user
            )
            project.req_skills.set(skills)
            project.save()

            for uid in selected_employee_ids:
                user = CustomUser.objects.get(id=uid)
                project.team_members.add(user)

           
            return redirect('manager_home')

        else:
            # First submission: get recommendations
            form = RecommendationForm(request.POST)
            if form.is_valid():
                skills = form.cleaned_data['skills']
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']
                num_people_required = form.cleaned_data['num_people_required']
                difficulty_level = form.cleaned_data['difficulty_level']
                preferred_role = form.cleaned_data['preferred_role']

                projectname = request.POST.get('projectname')
                projectdesc = request.POST.get('projectdesc')

                recommendations = recommend_employees(
                    skills=skills,
                    start_date=start_date,
                    end_date=end_date,
                    num_people_required=num_people_required,
                    difficulty_level=difficulty_level,
                    preferred_role=preferred_role.name if preferred_role else None
                )

                return render(request, 'manager/recommend_project.html', {
                    'form': form,
                    'recommendations': recommendations,
                    'projectname': projectname,
                    'projectdesc': projectdesc,
                    'skills': skills,
                    'start_date': start_date,
                    'end_date': end_date,
                    'difficulty_level': difficulty_level,
                    'num_people_required': num_people_required
                })

    else:
        form = RecommendationForm()

    return render(request, 'manager/recommend_project.html', {
        'form': form
    })
# task_recommend!!
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from .services import generate_task_suggestions
from .models import AddProject, Task

def recommend_task(request, project_id):
    project = get_object_or_404(AddProject, id=project_id)
    suggestions = generate_task_suggestions(project.projectdesc, project.end_date)
    tasks = project.tasks.all()

    return render(request, 'manager/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'suggestions': suggestions,
    })


from django.views.decorators.http import require_POST

@require_POST
def add_suggested_task(request, project_id):
    project = get_object_or_404(AddProject, id=project_id)
    title = request.POST.get("title", "")

    if title:
        Task.objects.create(
            project=project,
            title=title,
            description="Suggested by AI. Please update.",
            deadline=project.end_date,  # ✅ Fix: Add deadline ===
            estimated_time=8.0,         # Optional: give a default
        )

    return redirect(project_detail, pk=project_id)


  
