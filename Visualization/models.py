# from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone


class Sprint(models.Model):
    name = models.CharField(max_length=100, verbose_name="Sprint Name")
    # project = models.ForeignKey('ProjectManagement.Project', on_delete=models.CASCADE, related_name='sprints')
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    total_story_points = models.PositiveIntegerField(default=0, verbose_name="Total Story Points")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"
        ordering = ['-start_date']


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=200, verbose_name="Task Title")
    sprint = models.ForeignKey(
        Sprint,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True,
        verbose_name="Sprint"
    )
    story_points = models.PositiveIntegerField(default=1, verbose_name="Story Points")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo',
        verbose_name="Status"
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completed At")

    def save(self, *args, **kwargs):
        if self.status == 'done' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['-id']