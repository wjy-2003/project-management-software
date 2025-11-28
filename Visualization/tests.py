from datetime import date, timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Sprint, Task


class SprintModelTest(TestCase):
    """Sprint模型测试"""

    def test_create_sprint(self):
        """测试创建Sprint"""
        sprint = Sprint.objects.create(
            name="Sprint 1",
            start_date="2024-01-01",
            end_date="2024-01-14",
            total_story_points=100,
        )
        self.assertEqual(sprint.name, "Sprint 1")
        self.assertEqual(sprint.total_story_points, 100)

    def test_sprint_str(self):
        """测试Sprint字符串表示"""
        sprint = Sprint.objects.create(
            name="Sprint Alpha",
            start_date="2024-01-01",
            end_date="2024-01-14",
        )
        self.assertEqual(str(sprint), "Sprint Alpha")

    def test_sprint_ordering(self):
        """测试Sprint按开始日期倒序排列"""
        sprint1 = Sprint.objects.create(
            name="Sprint 1",
            start_date="2024-01-01",
            end_date="2024-01-14",
        )
        sprint2 = Sprint.objects.create(
            name="Sprint 2",
            start_date="2024-01-15",
            end_date="2024-01-28",
        )
        sprints = list(Sprint.objects.all())
        self.assertEqual(sprints[0], sprint2)  # 最新的在前
        self.assertEqual(sprints[1], sprint1)


class TaskModelTest(TestCase):
    """Task模型测试"""

    def setUp(self):
        self.sprint = Sprint.objects.create(
            name="Test Sprint",
            start_date="2024-01-01",
            end_date="2024-01-14",
            total_story_points=50,
        )

    def test_create_task(self):
        """测试创建任务"""
        task = Task.objects.create(
            title="开发登录功能",
            sprint=self.sprint,
            story_points=5,
            status="todo",
        )
        self.assertEqual(task.title, "开发登录功能")
        self.assertEqual(task.status, "todo")
        self.assertEqual(task.story_points, 5)

    def test_task_str(self):
        """测试任务字符串表示"""
        task = Task.objects.create(
            title="测试任务",
            sprint=self.sprint,
        )
        self.assertEqual(str(task), "测试任务")

    def test_task_auto_complete_time(self):
        """测试任务完成时自动记录完成时间"""
        task = Task.objects.create(
            title="测试自动完成时间",
            sprint=self.sprint,
            status="todo",
        )
        self.assertIsNone(task.completed_at)

        # 标记为完成
        task.status = "done"
        task.save()
        self.assertIsNotNone(task.completed_at)

    def test_task_without_sprint(self):
        """测试创建不关联Sprint的任务"""
        task = Task.objects.create(
            title="独立任务",
            story_points=3,
        )
        self.assertIsNone(task.sprint)
        self.assertEqual(task.story_points, 3)

    def test_task_status_choices(self):
        """测试任务状态选择"""
        task = Task.objects.create(
            title="状态测试",
            sprint=self.sprint,
        )

        # 测试所有状态
        task.status = "todo"
        task.save()
        self.assertEqual(task.status, "todo")

        task.status = "in_progress"
        task.save()
        self.assertEqual(task.status, "in_progress")

        task.status = "done"
        task.save()
        self.assertEqual(task.status, "done")


class BurndownChartViewTest(TestCase):
    """燃尽图视图测试"""

    def setUp(self):
        self.client = Client()
        self.sprint = Sprint.objects.create(
            name="Test Sprint",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            total_story_points=100,
        )

        # 创建一些任务
        Task.objects.create(
            title="任务1",
            sprint=self.sprint,
            story_points=20,
            status="done",
            completed_at=timezone.now(),
        )
        Task.objects.create(
            title="任务2",
            sprint=self.sprint,
            story_points=30,
            status="in_progress",
        )

    def test_burndown_chart_view(self):
        """测试燃尽图视图加载"""
        response = self.client.get(
            reverse(
                "Visualization:burndown_chart", kwargs={"sprint_id": self.sprint.id}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Sprint")
        self.assertTemplateUsed(response, "visualization/burndown_chart.html")

    def test_burndown_chart_context(self):
        """测试燃尽图上下文数据"""
        response = self.client.get(
            reverse(
                "Visualization:burndown_chart", kwargs={"sprint_id": self.sprint.id}
            )
        )
        self.assertIn("sprint", response.context)
        self.assertIn("dates", response.context)
        self.assertIn("ideal_burndown", response.context)
        self.assertIn("actual_burndown", response.context)

    def test_burndown_chart_nonexistent_sprint(self):
        """测试访问不存在的Sprint"""
        response = self.client.get(
            reverse("Visualization:burndown_chart", kwargs={"sprint_id": 9999})
        )
        self.assertEqual(response.status_code, 404)


class IntegrationTest(TestCase):
    """集成测试"""

    def test_sprint_task_relationship(self):
        """测试Sprint和Task的关联关系"""
        sprint = Sprint.objects.create(
            name="Integration Sprint",
            start_date="2024-01-01",
            end_date="2024-01-14",
            total_story_points=100,
        )

        # 创建多个任务
        task1 = Task.objects.create(
            title="任务1",
            sprint=sprint,
            story_points=20,
            status="done",
        )
        task2 = Task.objects.create(
            title="任务2",
            sprint=sprint,
            story_points=30,
            status="in_progress",
        )

        # 验证关联
        self.assertEqual(sprint.tasks.count(), 2)
        self.assertIn(task1, sprint.tasks.all())
        self.assertIn(task2, sprint.tasks.all())

    def test_task_completion_workflow(self):
        """测试任务完成工作流"""
        sprint = Sprint.objects.create(
            name="Workflow Sprint",
            start_date="2024-01-01",
            end_date="2024-01-14",
            total_story_points=50,
        )

        task = Task.objects.create(
            title="工作流任务",
            sprint=sprint,
            story_points=10,
            status="todo",
        )

        # 进行中
        task.status = "in_progress"
        task.save()
        self.assertEqual(task.status, "in_progress")
        self.assertIsNone(task.completed_at)

        # 完成
        task.status = "done"
        task.save()
        self.assertEqual(task.status, "done")
        self.assertIsNotNone(task.completed_at)
