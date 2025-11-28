from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Permission, Role, Team, TeamMember

User = get_user_model()


class PermissionModelTest(TestCase):
    """权限模型测试"""

    def test_create_permission(self):
        """测试创建权限"""
        perm = Permission.objects.create(code="view_project", label="查看项目")
        self.assertEqual(perm.code, "view_project")
        self.assertEqual(perm.label, "查看项目")

    def test_permission_str(self):
        """测试权限字符串表示"""
        perm = Permission.objects.create(code="edit_task", label="编辑任务")
        self.assertEqual(str(perm), "编辑任务")

    def test_permission_unique_code(self):
        """测试权限代码唯一性"""
        Permission.objects.create(code="test_perm", label="测试权限")
        with self.assertRaises(Exception):
            Permission.objects.create(code="test_perm", label="重复权限")


class RoleModelTest(TestCase):
    """角色模型测试"""

    def setUp(self):
        self.perm1 = Permission.objects.create(code="view_project", label="查看项目")
        self.perm2 = Permission.objects.create(code="edit_project", label="编辑项目")

    def test_create_role(self):
        """测试创建角色"""
        role = Role.objects.create(name="开发者", description="开发角色")
        self.assertEqual(role.name, "开发者")
        self.assertEqual(role.description, "开发角色")

    def test_role_str(self):
        """测试角色字符串表示"""
        role = Role.objects.create(name="测试工程师")
        self.assertEqual(str(role), "测试工程师")

    def test_role_permissions(self):
        """测试角色权限关联"""
        role = Role.objects.create(name="项目经理")
        role.permissions.add(self.perm1, self.perm2)
        self.assertEqual(role.permissions.count(), 2)

    def test_has_permission(self):
        """测试权限检查"""
        role = Role.objects.create(name="开发者")
        role.permissions.add(self.perm1)

        self.assertTrue(role.has_permission("view_project"))
        self.assertFalse(role.has_permission("edit_project"))


class TeamModelTest(TestCase):
    """团队模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="password123")

    def test_create_team(self):
        """测试创建团队"""
        team = Team.objects.create(
            name="开发团队", description="核心开发团队", owner=self.user
        )
        self.assertEqual(team.name, "开发团队")
        self.assertEqual(team.owner, self.user)

    def test_team_str(self):
        """测试团队字符串表示"""
        team = Team.objects.create(name="测试团队", owner=self.user)
        self.assertEqual(str(team), "测试团队")

    def test_team_unique_name(self):
        """测试团队名称唯一性"""
        Team.objects.create(name="唯一团队", owner=self.user)
        user2 = User.objects.create_user(username="user2", password="pass")
        with self.assertRaises(Exception):
            Team.objects.create(name="唯一团队", owner=user2)


class TeamMemberModelTest(TestCase):
    """团队成员模型测试"""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.member_user = User.objects.create_user(
            username="member", password="password123"
        )
        self.team = Team.objects.create(name="测试团队", owner=self.owner)
        self.role = Role.objects.create(name="开发者")

    def test_create_team_member(self):
        """测试创建团队成员"""
        member = TeamMember.objects.create(
            team=self.team, user=self.member_user, role=self.role
        )
        self.assertEqual(member.team, self.team)
        self.assertEqual(member.user, self.member_user)
        self.assertTrue(member.is_active)

    def test_team_member_str(self):
        """测试团队成员字符串表示"""
        member = TeamMember.objects.create(
            team=self.team, user=self.member_user, role=self.role
        )
        expected = f"{self.member_user.get_username()} @ {self.team} ({self.role})"
        self.assertEqual(str(member), expected)

    def test_team_member_unique_together(self):
        """测试团队成员唯一性约束"""
        TeamMember.objects.create(team=self.team, user=self.member_user, role=self.role)
        with self.assertRaises(Exception):
            TeamMember.objects.create(
                team=self.team, user=self.member_user, role=self.role
            )

    def test_has_permission(self):
        """测试成员权限检查"""
        perm = Permission.objects.create(code="view_task", label="查看任务")
        self.role.permissions.add(perm)

        member = TeamMember.objects.create(
            team=self.team, user=self.member_user, role=self.role, is_active=True
        )
        self.assertTrue(member.has_permission("view_task"))

        # 停用成员
        member.is_active = False
        member.save()
        self.assertFalse(member.has_permission("view_task"))


class TeamViewTest(TestCase):
    """团队视图测试"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.user.is_staff = True
        self.user.save()
        self.client.login(username="testuser", password="testpass123")
        self.role = Role.objects.create(name="Manager")

    def test_team_list_view(self):
        """测试团队列表视图"""
        team = Team.objects.create(name="测试团队", owner=self.user)
        TeamMember.objects.create(team=team, user=self.user, role=self.role)

        response = self.client.get(reverse("TeamManagement:team-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "测试团队")

    def test_team_detail_view(self):
        """测试团队详情视图"""
        team = Team.objects.create(name="详情团队", owner=self.user)
        TeamMember.objects.create(team=team, user=self.user, role=self.role)

        response = self.client.get(
            reverse("TeamManagement:team-detail", kwargs={"pk": team.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "详情团队")

    def test_team_create_view_get(self):
        """测试团队创建视图GET请求"""
        response = self.client.get(reverse("TeamManagement:team-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "TeamManagement/team_form.html")

    def test_team_create_view_post(self):
        """测试团队创建视图POST请求"""
        data = {
            "name": "新团队",
            "description": "这是一个新团队",
            "owner": self.user.id,
        }
        response = self.client.post(reverse("TeamManagement:team-create"), data)
        self.assertEqual(response.status_code, 302)  # 重定向
        self.assertTrue(Team.objects.filter(name="新团队").exists())

    def test_team_delete(self):
        """测试删除团队"""
        team = Team.objects.create(name="待删除团队", owner=self.user)
        TeamMember.objects.create(team=team, user=self.user, role=self.role)

        response = self.client.post(
            reverse("TeamManagement:team-delete", kwargs={"pk": team.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Team.objects.filter(pk=team.pk).exists())


class UserManagementViewTest(TestCase):
    """用户管理视图测试"""

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@test.com"
        )
        self.client.login(username="admin", password="admin123")

    def test_user_create_view(self):
        """测试用户创建视图"""
        data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post(reverse("TeamManagement:user-create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_update_view(self):
        """测试用户更新视图"""
        user = User.objects.create_user(
            username="updateuser", password="pass123", email="update@test.com"
        )
        data = {
            "username": "updateuser",
            "email": "newemail@test.com",
            "first_name": "Updated",
            "last_name": "User",
            "is_active": True,
            "is_staff": True,
        }
        self.client.post(
            reverse("TeamManagement:user-update", kwargs={"user_id": user.id}), data
        )
        user.refresh_from_db()
        response = user.email
        self.assertEqual(response, "newemail@test.com")

    def test_user_delete(self):
        """测试删除用户"""
        user = User.objects.create_user(username="deleteuser", password="pass123")
        response = self.client.post(
            reverse("TeamManagement:user-delete", kwargs={"user_id": user.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=user.id).exists())

    def test_cannot_delete_self(self):
        """测试不能删除自己的账号"""
        self.client.post(
            reverse("TeamManagement:user-delete", kwargs={"user_id": self.superuser.id})
        )
        response = User.objects.filter(pk=self.superuser.id)
        self.assertTrue(response.exists())


class IntegrationTest(TestCase):
    """集成测试"""

    def setUp(self):
        self.user = User.objects.create_user(username="manager", password="pass123")
        self.user.is_staff = True
        self.user.save()

    def test_complete_team_workflow(self):
        """测试完整的团队工作流"""
        # 1. 创建团队
        team = Team.objects.create(name="完整流程团队", owner=self.user)

        # 2. 创建角色和权限
        perm1 = Permission.objects.create(code="view_data", label="查看数据")
        perm2 = Permission.objects.create(code="edit_data", label="编辑数据")
        role = Role.objects.create(name="开发者", description="开发角色")
        role.permissions.add(perm1, perm2)

        # 3. 添加团队成员
        member_user = User.objects.create_user(username="dev", password="pass")
        member = TeamMember.objects.create(team=team, user=member_user, role=role)

        # 4. 验证权限
        self.assertTrue(member.has_permission("view_data"))
        self.assertTrue(member.has_permission("edit_data"))

        # 5. 验证团队关系
        self.assertEqual(team.members.count(), 1)
        self.assertIn(member, team.members.all())
