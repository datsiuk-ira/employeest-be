# api/models.py
from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    """
    Represents a project within the business. [cite: 53]
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True) [cite: 26, 53]
    # owner_id in the ERD suggests a link to the user who owns/created it. [cite: 54]
    # For simplicity, linking to Django's User model.
    owner = models.ForeignKey(User, related_name='owned_projects', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    """
    Represents a task within a project. [cite: 15, 51]
    """
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]

    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255) [cite: 54]
    description = models.TextField(blank=True, null=True) [cite: 54]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO') [cite: 54]
    # user_id in ERD implies assignee [cite: 54]
    assignee = models.ForeignKey(User, related_name='assigned_tasks', on_delete=models.SET_NULL, null=True, blank=True)
    story_points = models.IntegerField(null=True, blank=True) [cite: 54] # Also mentioned as part of task management [cite: 39]
    deadline = models.DateField(null=True, blank=True) # Mentioned in task creation [cite: 51]
    # estimation is mentioned[cite: 51], could be a DurationField or an IntegerField representing hours/days
    estimation_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Project: {self.project.name})"