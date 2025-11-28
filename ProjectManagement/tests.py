from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Document, Project, Task, TeamMember

User = get_user_model()


class TeamMemberModelTest(TestCase):
    """团队成员模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_team_member(self):
        """测试创建团队成员"""
        member = TeamMember.objects.create(user=self.user, role="开发者")
        self.assertEqual(member.user.username, "testuser")
        self.assertEqual(member.role, "开发者")
        self.assertIsNotNone(member.join_date)

    def test_team_member_str(self):
        """测试团队成员字符串表示"""
        member = TeamMember.objects.create(user=self.user, role="测试工程师")
        self.assertEqual(str(member), "testuser - 测试工程师")


class DocumentModelTest(TestCase):
    """文档模型测试"""

    def test_create_document(self):
        """测试创建文档"""
        doc = Document.objects.create(title="测试文档", description="这是一个测试文档")
        self.assertEqual(doc.title, "测试文档")
        self.assertEqual(doc.description, "这是一个测试文档")
        self.assertIsNotNone(doc.upload_date)

    def test_document_str(self):
        """测试文档字符串表示"""
        doc = Document.objects.create(title="需求文档")
        self.assertEqual(str(doc), "需求文档")


class TaskModelTest(TestCase):
    """任务模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="developer", password="devpass123"
        )
        self.member = TeamMember.objects.create(user=self.user, role="开发者")
        self.project = Project.objects.create(
            project_number="PRJ001",
            title="测试项目",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
            available_workdays=200,
        )

    def test_create_task(self):
        """测试创建任务"""
        task = Task.objects.create(
            project=self.project,
            title="开发登录功能",
            description="实现用户登录功能",
            estimated_hours=40,
            consumed_hours=0,
            remaining_hours=40,
        )
        self.assertEqual(task.title, "开发登录功能")
        self.assertEqual(task.status, "not_started")
        self.assertEqual(task.estimated_hours, 40)

    def test_task_auto_status_update(self):
        """测试任务状态自动更新"""
        task = Task.objects.create(
            project=self.project,
            title="测试任务",
            estimated_hours=10,
            consumed_hours=0,
            remaining_hours=10,
        )

        # 未开始
        self.assertEqual(task.status, "not_started")

        # 进行中
        task.consumed_hours = 5
        task.save()
        self.assertEqual(task.status, "in_progress")
        self.assertEqual(task.remaining_hours, 5)

        # 已完成
        task.consumed_hours = 10
        task.save()
        self.assertEqual(task.status, "completed")
        self.assertEqual(task.remaining_hours, 0)

    def test_task_force_status(self):
        """测试强制状态参数"""
        task = Task.objects.create(
            project=self.project,
            title="暂停任务",
            estimated_hours=10,
            consumed_hours=5,
            remaining_hours=5,
        )
        task.status = "suspended"
        task.save(force_status=True)
        self.assertEqual(task.status, "suspended")

    def test_task_progress_calculation(self):
        """测试任务进度计算"""
        task = Task.objects.create(
            project=self.project,
            title="进度测试",
            estimated_hours=100,
            consumed_hours=50,
            remaining_hours=50,
        )
        self.assertEqual(task.get_task_progress(), 50.0)

        task.consumed_hours = 75
        task.save()
        self.assertEqual(task.get_task_progress(), 75.0)

    def test_task_with_assigned_member(self):
        """测试分配任务给成员"""
        task = Task.objects.create(
            project=self.project,
            title="分配任务",
            assigned_to=self.member,
            estimated_hours=20,
            consumed_hours=0,
            remaining_hours=20,
        )
        self.assertEqual(task.assigned_to.user.username, "developer")


class ProjectModelTest(TestCase):
    """项目模型测试"""

    def setUp(self):
        self.user1 = User.objects.create_user(username="pm", password="pmpass123")
        self.user2 = User.objects.create_user(username="dev", password="devpass123")
        self.member1 = TeamMember.objects.create(user=self.user1, role="项目经理")
        self.member2 = TeamMember.objects.create(user=self.user2, role="开发者")

    def test_create_project(self):
        """测试创建项目"""
        project = Project.objects.create(
            project_number="PRJ2024001",
            title="Web应用开发",
            description="开发企业级Web应用",
            planned_start_date="2024-01-01",
            planned_end_date="2024-06-30",
            estimated_hours=2000,
            available_workdays=120,
        )
        self.assertEqual(project.project_number, "PRJ2024001")
        self.assertEqual(project.title, "Web应用开发")
        self.assertEqual(project.status, "planning")

    def test_project_str(self):
        """测试项目字符串表示"""
        project = Project.objects.create(
            project_number="PRJ001",
            title="测试项目",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
        )
        self.assertEqual(str(project), "PRJ001 - 测试项目")

    def test_project_progress_calculation(self):
        """测试项目进度计算"""
        project = Project.objects.create(
            project_number="PRJ002",
            title="进度测试项目",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
            consumed_hours=250,
        )
        self.assertEqual(project.get_project_progress(), 25.0)

    def test_project_update_remaining_hours(self):
        """测试更新剩余工时"""
        project = Project.objects.create(
            project_number="PRJ003",
            title="工时测试",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=500,
            consumed_hours=200,
        )
        project.update_project_remaining_hours()
        self.assertEqual(project.remaining_hours, 300)

    def test_project_team_members(self):
        """测试项目团队成员关联"""
        project = Project.objects.create(
            project_number="PRJ004",
            title="团队测试",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
        )
        project.team_members.add(self.member1, self.member2)
        self.assertEqual(project.team_members.count(), 2)

    def test_project_documents(self):
        """测试项目文档关联"""
        project = Project.objects.create(
            project_number="PRJ005",
            title="文档测试",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
        )
        doc1 = Document.objects.create(title="需求文档")
        doc2 = Document.objects.create(title="设计文档")
        project.documents.add(doc1, doc2)
        self.assertEqual(project.documents.count(), 2)


class ProjectViewTest(TestCase):
    """项目视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.project = Project.objects.create(
            project_number="PRJ001",
            title="测试项目",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
            available_workdays=200,
        )

    def test_project_list_view(self):
        """测试项目列表视图"""
        response = self.client.get(reverse("projectmanagement:project_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "测试项目")
        self.assertTemplateUsed(response, "projectmanagement/project_list.html")

    def test_project_info_view(self):
        """测试项目详情视图"""
        response = self.client.get(
            reverse(
                "projectmanagement:project_info",
                kwargs={"project_number": "PRJ001"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PRJ001")
        self.assertTemplateUsed(response, "projectmanagement/project_info.html")

    def test_project_create_view_get(self):
        """测试项目创建视图GET请求"""
        response = self.client.get(reverse("projectmanagement:project_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projectmanagement/project_form.html")

    def test_project_create_view_post(self):
        """测试项目创建视图POST请求"""
        data = {
            "project_number": "PRJ002",
            "title": "新项目",
            "description": "这是一个新项目",
            "planned_start_date": "2024-02-01",
            "planned_end_date": "2024-08-31",
            "estimated_hours": 500,
            "available_workdays": 100,
            "status": "planning",
        }
        response = self.client.post(reverse("projectmanagement:project_create"), data)
        self.assertEqual(response.status_code, 302)  # 重定向
        self.assertTrue(Project.objects.filter(project_number="PRJ002").exists())

    def test_project_edit_view(self):
        """测试项目编辑视图"""
        response = self.client.get(
            reverse(
                "projectmanagement:project_edit",
                kwargs={"project_number": "PRJ001"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projectmanagement/project_edit.html")

    def test_project_cancel(self):
        """测试取消项目"""
        response = self.client.post(
            reverse(
                "projectmanagement:project_cancel",
                kwargs={"project_number": "PRJ001"},
            )
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "cancelled")
        self.assertEqual(response.status_code, 302)

    def test_project_pause(self):
        """测试暂停项目"""
        self.project.status = "in_progress"
        self.project.save()

        self.client.post(
            reverse(
                "projectmanagement:project_pause",
                kwargs={"project_number": "PRJ001"},
            )
        )
        self.project.refresh_from_db()
        response = self.project.status
        self.assertEqual(response, "suspended")

    def test_project_resume(self):
        """测试恢复项目"""
        self.project.status = "suspended"
        self.project.save()

        self.client.post(
            reverse(
                "projectmanagement:project_resume",
                kwargs={"project_number": "PRJ001"},
            )
        )
        self.project.refresh_from_db()
        response = self.project.status
        self.assertEqual(response, "in_progress")


class TaskViewTest(TestCase):
    """任务视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.project = Project.objects.create(
            project_number="PRJ001",
            title="测试项目",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
        )

        self.member = TeamMember.objects.create(user=self.user, role="开发者")

    def test_task_create_view_get(self):
        """测试任务创建视图GET请求"""
        response = self.client.get(
            reverse(
                "projectmanagement:task_create",
                kwargs={"project_number": "PRJ001"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projectmanagement/task_form.html")

    def test_task_create_view_post(self):
        """测试任务创建视图POST请求"""
        data = {
            "title": "新任务",
            "description": "任务描述",
            "estimated_hours": 20,
            "consumed_hours": 0,
            "remaining_hours": 20,
            "status": "not_started",
        }
        self.client.post(
            reverse(
                "projectmanagement:task_create",
                kwargs={"project_number": "PRJ001"},
            ),
            data,
        )
        # 检查是否创建成功并重定向
        response = Task.objects.filter(title="新任务")
        self.assertTrue(response.exists())


class DocumentViewTest(TestCase):
    """文档视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.project = Project.objects.create(
            project_number="PRJ001",
            title="测试项目",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
        )

    def test_document_create_view_get(self):
        """测试文档创建视图GET请求"""
        response = self.client.get(
            reverse(
                "projectmanagement:document_create",
                kwargs={"project_number": "PRJ001"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projectmanagement/document_form.html")


class MemberManageViewTest(TestCase):
    """成员管理视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.project = Project.objects.create(
            project_number="PRJ001",
            title="测试项目",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
        )

    def test_members_manage_view(self):
        """测试成员管理视图"""
        response = self.client.get(
            reverse(
                "projectmanagement:project_members_manage",
                kwargs={"project_number": "PRJ001"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projectmanagement/members_manage.html")


class IntegrationTest(TestCase):
    """集成测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="manager", password="manager123")
        self.client.login(username="manager", password="manager123")

    def test_complete_project_workflow(self):
        """测试完整的项目工作流"""
        # 1. 创建项目
        project = Project.objects.create(
            project_number="PRJ2024",
            title="集成测试项目",
            planned_start_date="2024-01-01",
            planned_end_date="2024-12-31",
            estimated_hours=1000,
            available_workdays=200,
        )

        # 2. 添加团队成员
        member = TeamMember.objects.create(user=self.user, role="开发者")
        project.team_members.add(member)

        # 3. 创建任务
        task = Task.objects.create(
            project=project,
            title="开发功能A",
            estimated_hours=100,
            consumed_hours=0,
            remaining_hours=100,
            assigned_to=member,
        )

        # 4. 更新任务进度
        task.consumed_hours = 50
        task.save()

        # 5. 验证状态
        self.assertEqual(task.status, "in_progress")
        self.assertEqual(task.remaining_hours, 50)
        self.assertEqual(task.get_task_progress(), 50.0)

        # 6. 完成任务
        task.consumed_hours = 100
        task.save()
        self.assertEqual(task.status, "completed")

        # 7. 验证项目可以正常访问
        response = self.client.get(
            reverse(
                "projectmanagement:project_info",
                kwargs={"project_number": "PRJ2024"},
            )
        )
        self.assertEqual(response.status_code, 200)
