from .models import UserProfile

def recommend_employees(skills, start_date, end_date, num_people_required, difficulty_level, preferred_role=None):
    candidates = UserProfile.objects.filter(availability=True)

    if preferred_role:
        candidates = candidates.filter(preferred_roles__name__icontains=preferred_role).distinct()

    recommendations = []

    for candidate in candidates:
        score = 0

        # Skill match
        candidate_skills = set(candidate.skills.all())
        required_skills = set(skills)
        skill_match_count = len(candidate_skills & required_skills)
        skill_score = (skill_match_count / len(required_skills)) * 40  # 40% weight
        score += skill_score

        # Experience (normalize: assume max 10 years cap for calculation)
        experience_score = min(candidate.experience, 10) / 10 * 20  # 20% weight
        score += experience_score

        # Availability (already filtered but still...)
        availability_score = 20  # Full marks for available
        score += availability_score

        # Load balancing
        load_score = (1 / (1 + candidate.current_load)) * 10  # 10% weight
        score += load_score

        # Level match
        level_score = 0
        if difficulty_level == 'easy' and candidate.level == 'junior':
            level_score = 10
        elif difficulty_level == 'medium' and candidate.level == 'mid':
            level_score = 10
        elif difficulty_level == 'hard' and candidate.level == 'senior':
            level_score = 10
        score += level_score

        recommendations.append({
            'user': candidate.user,
            'score': score
        })

    # Sort descending by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    # Return top N employees
    return recommendations[:num_people_required]
