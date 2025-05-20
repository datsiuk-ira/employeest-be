from django.db.models import Count, Sum
from django.utils import timezone
from django.db.models.functions import TruncMonth, TruncWeek
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Project, Task, WorkLog
from .permissions import IsProjectOwner, IsAssigneeOrProjectOwner, IsWorkLogOwner
from .serializers import ProjectSerializer, TaskSerializer, WorkLogSerializer
from .filters import TaskFilter
from .quickchart_helper import get_chart_url
from .chart_templates import (
    get_base_pie_chart_config,
    get_base_bar_chart_config,
    get_base_line_chart_config
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().prefetch_related('tasks')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsProjectOwner]
        elif self.action == 'task_status_chart':
            self.permission_classes = [permissions.IsAuthenticated,
                                       IsProjectOwner]
        else:
            self.permission_classes = [
                permissions.IsAuthenticated]
        return super().get_permissions()

    @action(detail=True, methods=['get'], url_path='velocity-chart',
            permission_classes=[permissions.IsAuthenticated, IsProjectOwner])
    def project_velocity_chart(self, request, pk=None):
        project = self.get_object()
        # За замовчуванням - щотижнева швидкість за останні 3 місяці
        three_months_ago = timezone.now() - timezone.timedelta(days=90)

        velocity_data = Task.objects.filter(
            project=project,
            status='DONE',
            story_points__isnull=False,
            updated_at__gte=three_months_ago
        ).annotate(
            period_start=TruncWeek('updated_at')
        ).values('period_start').annotate(
            total_story_points=Sum('story_points')
        ).order_by('period_start')

        if not velocity_data:
            return Response({"message": "Not enough data to calculate project velocity."}, status=404)

        labels = [item['period_start'].strftime('%Y-W%W') for item in velocity_data]
        data = [item['total_story_points'] for item in velocity_data]

        chart_config = get_base_line_chart_config()
        chart_config['data']['labels'] = labels
        chart_config['data']['datasets'][0]['label'] = f'Project Velocity (Story Points per Week)'
        chart_config['data']['datasets'][0]['data'] = data
        chart_config['options']['plugins']['title']['text'] = f'Velocity for Project: {project.name}'

        chart_url = get_chart_url(chart_config)
        if chart_url:
            return Response({'chart_url': chart_url})
        else:
            return Response({'error': 'Could not generate chart URL.'}, status=500)

    @action(detail=True, methods=['get'], url_path='task-status-chart')
    def task_status_chart(self, request, pk=None):
        project = self.get_object()
        task_statuses = project.tasks.values('status').annotate(count=Count('status')).order_by('status')

        if not task_statuses:
            return Response({"message": "No tasks found for this project to generate a chart."}, status=404)

        labels = [item['status'] for item in task_statuses]
        data = [item['count'] for item in task_statuses]

        chart_config = get_base_pie_chart_config()
        chart_config['data']['labels'] = labels
        chart_config['data']['datasets'][0]['data'] = data
        chart_config['options']['plugins']['title']['text'] = f'Task Status Distribution for {project.name}'
        # Can customize color
        # default_colors = chart_config['data']['datasets'][0]['backgroundColor']
        # chart_config['data']['datasets'][0]['backgroundColor'] = [default_colors[i % len(default_colors)] for i in range(len(labels))]

        chart_url = get_chart_url(chart_config)
        if chart_url:
            return Response({'chart_url': chart_url})
        else:
            return Response({'error': 'Could not generate chart URL.'}, status=500)


class BusinessStatisticsViews(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        one_year_ago = timezone.now() - timezone.timedelta(days=365)

        completed_tasks_monthly = Task.objects.filter(
            status='DONE',
            updated_at__gte=one_year_ago,
            story_points__isnull=False
        ).annotate(
            month=TruncMonth('updated_at')
        ).values('month').annotate(
            total_story_points=Sum('story_points')
        ).order_by('month')

        if not completed_tasks_monthly:
            return Response({"message": "No completed tasks with story points found for the last year."}, status=404)

        labels = [item['month'].strftime('%Y-%m') for item in completed_tasks_monthly]
        data = [item['total_story_points'] for item in completed_tasks_monthly]

        chart_config = get_base_bar_chart_config()
        chart_config['data']['labels'] = labels
        chart_config['data']['datasets'][0]['label'] = 'Completed Story Points'
        chart_config['data']['datasets'][0]['data'] = data
        chart_config['options']['plugins']['title']['text'] = 'Monthly Completed Story Points (Last Year)'
        # Can customize color
        # chart_config['data']['datasets'][0]['backgroundColor'] = 'rgba(54, 162, 235, 0.7)'
        # chart_config['data']['datasets'][0]['borderColor'] = 'rgba(54, 162, 235, 1)'

        chart_url = get_chart_url(chart_config)
        if chart_url:
            return Response({'chart_url': chart_url})
        else:
            return Response({'error': 'Could not generate chart URL.'}, status=500)


class UserPersonalStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        one_year_ago = timezone.now() - timezone.timedelta(days=365)

        completed_tasks_monthly = Task.objects.filter(
            assignee=user,
            status='DONE',
            updated_at__gte=one_year_ago
        ).annotate(
            month=TruncMonth('updated_at')
        ).values('month').annotate(
            tasks_count=Count('id')
        ).order_by('month')

        if not completed_tasks_monthly:
            return Response({"message": "You have no completed tasks in the last year."}, status=404)

        labels = [item['month'].strftime('%Y-%m') for item in completed_tasks_monthly]
        data = [item['tasks_count'] for item in completed_tasks_monthly]

        chart_config = get_base_line_chart_config()
        chart_config['data']['labels'] = labels
        chart_config['data']['datasets'][0]['label'] = 'My Completed Tasks'
        chart_config['data']['datasets'][0]['data'] = data
        chart_config['options']['plugins']['title']['text'] = 'My Monthly Task Completions (Last Year)'
        # Can customize color
        # chart_config['data']['datasets'][0]['borderColor'] = 'rgba(255, 99, 132, 0.9)'
        # chart_config['data']['datasets'][0]['backgroundColor'] = 'rgba(255, 99, 132, 0.2)'

        chart_url = get_chart_url(chart_config)
        if chart_url:
            return Response({'chart_url': chart_url})
        else:
            return Response({'error': 'Could not generate chart URL.'}, status=500)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().select_related('project', 'assignee')
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['name', 'description', 'project__name']
    ordering_fields = ['created_at', 'deadline', 'status', 'name']
    ordering = ['-created_at']

    # def get_permissions(self):
    #     if self.action in ['update', 'partial_update', 'destroy']:
    #             self.permission_classes = [permissions.IsAuthenticated, IsAssigneeOrProjectOwner]
    #         elif self.action in ['start_progress', 'mark_as_done']:
    #             self.permission_classes = [permissions.IsAuthenticated, IsAssigneeOrProjectOwner]
    #         else:
    #             self.permission_classes = [permissions.IsAuthenticated]
    #         return super().get_permissions()

    @action(detail=True, methods=['post'], url_path='start-progress',
            permission_classes=[permissions.IsAuthenticated, IsAssigneeOrProjectOwner])
    def start_progress(self, request, pk=None):
        task = self.get_object()
        if task.status == 'TODO':
            task.status = 'IN_PROGRESS'
            task.save()
            return Response({'status': 'Task moved to In Progress', 'task_status': task.status})
        return Response({'status': 'Task cannot be moved to In Progress from current state'}, status=400)

    @action(detail=True, methods=['post'], url_path='mark-as-done', permission_classes=[permissions.IsAuthenticated, IsAssigneeOrProjectOwner])
    def mark_as_done(self, request, pk=None):
        task = self.get_object()
        if task.status == 'IN_PROGRESS':
            task.status = 'DONE'
            task.completed_at = timezone.now()
            task.updated_at = timezone.now()
            task.save()
            return Response({'status': 'Task marked as Done', 'task_status': task.status})
        return Response({'status': 'Task cannot be marked as Done from current state'}, status=400)

class WorkLogViewSet(viewsets.ModelViewSet):
    queryset = WorkLog.objects.all()
    serializer_class = WorkLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return WorkLog.objects.all()
        return WorkLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsWorkLogOwner()]
        return super().get_permissions()


class OwnerDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated] # switch to IsBusinessOwner later

    def get(self, request, format=None):
        user = request.user
        if not user.profile.is_owner:
            return Response({"detail": "Not authorized"}, status=403)

        owned_projects = Project.objects.filter(owner=user)
        active_projects_count = owned_projects.filter(tasks__status__in=['TODO', 'IN_PROGRESS']).distinct().count()
        total_projects_count = owned_projects.count()

        tasks_in_owned_projects = Task.objects.filter(project__owner=user)
        total_tasks = tasks_in_owned_projects.count()
        todo_tasks = tasks_in_owned_projects.filter(status='TODO').count()
        inprogress_tasks = tasks_in_owned_projects.filter(status='IN_PROGRESS').count()
        done_tasks = tasks_in_owned_projects.filter(status='DONE').count()

        projects_data = ProjectSerializer(owned_projects, many=True, context={'request': request}).data
        # business_stats_chart_url = request.build_absolute_uri(reverse('business-stats-story-points'))


        dashboard_data = {
            'summary_stats': {
                'total_projects': total_projects_count,
                'active_projects': active_projects_count,
                'total_tasks': total_tasks,
                'tasks_todo': todo_tasks,
                'tasks_inprogress': inprogress_tasks,
                'tasks_done': done_tasks,
            },
            'projects_list': projects_data,
            # 'charts': {
            #     'business_story_points_monthly_url': business_stats_chart_url,
            # }
        }
        return Response(dashboard_data)


class EmployeeDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user

        assigned_task_projects_ids = Task.objects.filter(assignee=user).values_list('project_id', flat=True).distinct()
        involved_projects = Project.objects.filter(id__in=assigned_task_projects_ids)
        projects_data = ProjectSerializer(involved_projects, many=True, context={'request': request}).data

        # add logic for Team

        current_tasks = Task.objects.filter(assignee=user, status__in=['TODO', 'IN_PROGRESS'])
        current_tasks_data = TaskSerializer(current_tasks, many=True, context={'request': request}).data

        # personal_task_completion_chart_url = request.build_absolute_uri(reverse('user-personal-task-stats'))


        dashboard_data = {
            'my_projects': projects_data,
            'my_teams': [],
            'my_current_tasks': current_tasks_data,
            # 'charts': {
            #     'task_completion_url': personal_task_completion_chart_url,
            # }
        }
        return Response(dashboard_data)