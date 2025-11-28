import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .src.security import GitPathValidationError, sanitize_path_string

User = get_user_model()


class SecurityTest(TestCase):
    """安全相关测试"""

    def test_sanitize_path_string(self):
        """测试路径字符串清理"""
        # 正常路径
        clean_path = sanitize_path_string("C:/projects/my-repo")
        self.assertIsInstance(clean_path, str)

        # 包含空格的路径
        clean_path = sanitize_path_string("C:/projects/my repo")
        self.assertIn("my repo", clean_path)

    def test_path_validation_empty(self):
        """测试空路径验证"""
        from .src.security import validate_git_repository_path

        with self.assertRaises(GitPathValidationError):
            validate_git_repository_path("")


class GitGraphViewTest(TestCase):
    """Git图形视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_git_graph_view_loads(self):
        """测试Git图形视图加载"""
        response = self.client.get(reverse("GitIntegration:git_graph"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "GitIntegration/git_graph.html")

    def test_git_graph_with_path_parameter(self):
        """测试带路径参数的Git图形视图"""
        response = self.client.get(
            reverse("GitIntegration:git_graph") + "?git_path=/test/repo"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("current_git_path", response.context)


class GitCommitViewTest(TestCase):
    """Git提交视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_git_commit_view_loads(self):
        """测试Git提交视图加载"""
        response = self.client.get(reverse("GitIntegration:git_commit"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "GitIntegration/git_commit.html")


class GitConflictsViewTest(TestCase):
    """Git冲突视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_git_conflicts_view_loads(self):
        """测试Git冲突视图加载"""
        response = self.client.get(reverse("GitIntegration:git_conflicts"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "GitIntegration/git_conflicts.html")


class GitPathAPITest(TestCase):
    """Git路径API测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    @patch("GitIntegration.views.validate_git_repository_path")
    def test_set_git_path_api(self, mock_validate):
        """测试设置Git路径API"""
        from pathlib import Path

        mock_validate.return_value = Path("/valid/repo")

        data = {"git_path": "/valid/repo"}
        response = self.client.post(
            reverse("GitIntegration:set_git_path"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])

    def test_set_git_path_empty(self):
        """测试设置空路径"""
        data = {"git_path": ""}
        response = self.client.post(
            reverse("GitIntegration:set_git_path"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertFalse(result["success"])

    def test_set_git_path_invalid_json(self):
        """测试设置路径时发送无效JSON"""
        response = self.client.post(
            reverse("GitIntegration:set_git_path"),
            data="invalid json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("GitIntegration.views.get_git_repository_path")
    def test_get_git_path_api(self, mock_get_path):
        """测试获取Git路径API"""
        from pathlib import Path

        mock_get_path.return_value = Path("/test/repo")

        response = self.client.get(reverse("GitIntegration:get_git_path"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])
        self.assertIn("git_path", result)


class GitStatusAPITest(TestCase):
    """Git状态API测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    @patch("GitIntegration.views.GitStatus")
    @patch("GitIntegration.views.get_git_repository_path")
    def test_git_status_api(self, mock_get_path, mock_git_status):
        """测试Git状态API"""
        from pathlib import Path

        mock_get_path.return_value = Path("/test/repo")
        mock_status_instance = MagicMock()
        mock_status_instance.get_status.return_value = {
            "branch": "main",
            "modified": [],
            "staged": [],
        }
        mock_git_status.return_value = mock_status_instance

        response = self.client.get(reverse("GitIntegration:git_status_api"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])
        self.assertIn("status", result)


class GitCommitAPITest(TestCase):
    """Git提交API测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_commit_without_message(self):
        """测试没有消息的提交"""
        data = {"message": ""}
        response = self.client.post(
            reverse("GitIntegration:git_commit_changes"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertFalse(result["success"])

    @patch("GitIntegration.views.GitStatus")
    @patch("GitIntegration.views.get_git_repository_path")
    def test_commit_with_message(self, mock_get_path, mock_git_status):
        """测试带消息的提交"""
        from pathlib import Path

        mock_get_path.return_value = Path("/test/repo")
        mock_status_instance = MagicMock()
        mock_status_instance.commit.return_value = {
            "success": True,
            "message": "Committed successfully",
        }
        mock_git_status.return_value = mock_status_instance

        data = {"message": "Test commit message"}
        response = self.client.post(
            reverse("GitIntegration:git_commit_changes"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])


class GitStageAPITest(TestCase):
    """Git暂存API测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_stage_without_files(self):
        """测试没有文件的暂存"""
        data = {"files": [], "stage": True}
        response = self.client.post(
            reverse("GitIntegration:git_stage_files"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("GitIntegration.views.GitStatus")
    @patch("GitIntegration.views.get_git_repository_path")
    def test_stage_files(self, mock_get_path, mock_git_status):
        """测试暂存文件"""
        from pathlib import Path

        mock_get_path.return_value = Path("/test/repo")
        mock_status_instance = MagicMock()
        mock_status_instance.stage_files.return_value = {
            "success": True,
            "message": "Files staged",
        }
        mock_git_status.return_value = mock_status_instance

        data = {"files": ["file1.py", "file2.py"], "stage": True}
        response = self.client.post(
            reverse("GitIntegration:git_stage_files"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])


class GitBranchAPITest(TestCase):
    """Git分支API测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    @patch("GitIntegration.views.GitOperations")
    @patch("GitIntegration.views.get_git_repository_path")
    def test_get_branches(self, mock_get_path, mock_git_ops):
        """测试获取分支列表"""
        from pathlib import Path

        mock_get_path.return_value = Path("/test/repo")
        mock_ops_instance = MagicMock()
        mock_ops_instance.get_branches.return_value = [
            {"name": "main", "current": True},
            {"name": "develop", "current": False},
        ]
        mock_git_ops.return_value = mock_ops_instance

        response = self.client.get(reverse("GitIntegration:git_branches"))
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])
        self.assertEqual(len(result["branches"]), 2)

    def test_create_branch_without_name(self):
        """测试创建分支时没有名称"""
        data = {"branch_name": ""}
        response = self.client.post(
            reverse("GitIntegration:git_create_branch"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("GitIntegration.views.GitOperations")
    @patch("GitIntegration.views.get_git_repository_path")
    def test_create_branch(self, mock_get_path, mock_git_ops):
        """测试创建分支"""
        from pathlib import Path

        mock_get_path.return_value = Path("/test/repo")
        mock_ops_instance = MagicMock()
        mock_ops_instance.create_branch.return_value = {
            "success": True,
            "message": "Branch created",
        }
        mock_git_ops.return_value = mock_ops_instance

        data = {"branch_name": "feature/new-feature", "switch": False}
        response = self.client.post(
            reverse("GitIntegration:git_create_branch"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])


class IntegrationTest(TestCase):
    """集成测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="integration", password="test123")
        self.client.login(username="integration", password="test123")

    @patch("GitIntegration.views.validate_git_repository_path")
    @patch("GitIntegration.views.GitStatus")
    def test_complete_git_workflow(self, mock_git_status, mock_validate):
        """测试完整的Git工作流"""
        from pathlib import Path

        # 设置路径
        mock_validate.return_value = Path("/test/repo")
        data = {"git_path": "/test/repo"}
        response = self.client.post(
            reverse("GitIntegration:set_git_path"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(response.json()["success"])

        # 验证会话中保存了路径
        session = self.client.session
        self.assertIn("git_path", session)
