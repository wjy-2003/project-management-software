# from django.shortcuts import render

# Create your views here.



from django.shortcuts import render, get_object_or_404
from django.db import models  
from datetime import timedelta
from .models import Sprint
import json


def burndown_chart_view(request, sprint_id):
    sprint = get_object_or_404(Sprint, id=sprint_id)

    delta = sprint.end_date - sprint.start_date
    dates = [(sprint.start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]

    total_points = sprint.total_story_points
    ideal_burndown = []
    for i, date in enumerate(dates):
        remaining = total_points - (total_points * i / len(dates))
        ideal_burndown.append(round(remaining, 1))

    actual_burndown = []
    for current_date in [sprint.start_date + timedelta(days=i) for i in range(delta.days + 1)]:
        completed_points = sprint.tasks.filter(
            status='done',
            completed_at__date__lte=current_date
        ).aggregate(total=models.Sum('story_points'))['total'] or 0

        remaining = total_points - completed_points
        actual_burndown.append(max(0, remaining))  

    context = {
        'sprint': sprint,
        'dates': json.dumps(dates),                    
        'ideal_burndown': json.dumps(ideal_burndown),  
        'actual_burndown': json.dumps(actual_burndown),
    }

    return render(request, 'visualization/burndown_chart.html', context)