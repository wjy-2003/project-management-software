# from django.test import TestCase

"""
单元测试
"""
from django.test import TestCase
from .session_manager import session_manager


class SessionManagerTestCase(TestCase):
    """会话管理器测试"""
    
    def setUp(self):
        """测试前清理会话"""
        # 清空所有会话（仅用于测试）
        session_manager.active_sessions.clear()
    
    def test_create_session(self):
        """测试创建会话"""
        session_id = session_manager.create_session("alice")
        
        self.assertIsNotNone(session_id)
        self.assertTrue(session_manager.session_exists(session_id))
        
        session = session_manager.get_session(session_id)
        self.assertEqual(session['initiator'], "alice")
        self.assertIn("alice", session['members'])
    
    def test_add_member(self):
        """测试添加成员"""
        session_id = session_manager.create_session("alice")
        
        # 添加编辑者
        success = session_manager.add_member(session_id, "bob", role="editor")
        self.assertTrue(success)
        
        # 验证成员已添加
        members = session_manager.get_all_members(session_id)
        self.assertEqual(len(members), 2)
        
        # 检查角色
        role = session_manager.get_member_role(session_id, "bob")
        self.assertEqual(role, "editor")
    
    def test_remove_member(self):
        """测试移除成员"""
        session_id = session_manager.create_session("alice")
        session_manager.add_member(session_id, "bob", role="editor")
        
        # 移除成员
        destroyed = session_manager.remove_member(session_id, "bob")
        self.assertFalse(destroyed)  # 还有 alice，会话不应销毁
        
        members = session_manager.get_all_members(session_id)
        self.assertEqual(len(members), 1)
    
    def test_session_destroyed_when_empty(self):
        """测试会话在最后一个成员离开时销毁"""
        session_id = session_manager.create_session("alice")
        
        # 移除唯一的成员
        destroyed = session_manager.remove_member(session_id, "alice")
        self.assertTrue(destroyed)
        
        # 会话应该不存在了
        self.assertFalse(session_manager.session_exists(session_id))
    
    def test_permission_check(self):
        """测试权限检查"""
        session_id = session_manager.create_session("alice")
        session_manager.add_member(session_id, "bob", role="editor")
        session_manager.add_member(session_id, "charlie", role="viewer")
        
        # 检查编辑权限
        self.assertTrue(session_manager.can_edit(session_id, "alice"))
        self.assertTrue(session_manager.can_edit(session_id, "bob"))
        self.assertFalse(session_manager.can_edit(session_id, "charlie"))
        
        # 检查发起者身份
        self.assertTrue(session_manager.is_initiator(session_id, "alice"))
        self.assertFalse(session_manager.is_initiator(session_id, "bob"))
    
    def test_update_member_role(self):
        """测试更新成员角色"""
        session_id = session_manager.create_session("alice")
        session_manager.add_member(session_id, "bob", role="viewer")
        
        # 更新角色
        success = session_manager.update_member_role(session_id, "bob", "editor")
        self.assertTrue(success)
        
        # 验证角色已更新
        role = session_manager.get_member_role(session_id, "bob")
        self.assertEqual(role, "editor")
    
    def test_cannot_update_initiator_role(self):
        """测试不能更新发起者角色"""
        session_id = session_manager.create_session("alice")
        
        # 尝试更新发起者角色应该失败
        success = session_manager.update_member_role(session_id, "alice", "viewer")
        self.assertFalse(success)
    
    def test_structure_operations(self):
        """测试文件夹结构操作"""
        session_id = session_manager.create_session("alice")
        
        # 获取初始结构
        structure = session_manager.get_structure(session_id)
        self.assertEqual(len(structure['folders']), 0)
        self.assertEqual(len(structure['files']), 0)
        
        # 添加文件夹
        structure['folders'].append({
            'id': 'f1',
            'name': 'src',
            'parent_id': None
        })
        
        # 更新结构
        success = session_manager.update_structure(session_id, structure)
        self.assertTrue(success)
        
        # 验证结构已更新
        updated_structure = session_manager.get_structure(session_id)
        self.assertEqual(len(updated_structure['folders']), 1)
        self.assertEqual(updated_structure['folders'][0]['name'], 'src')
    
    def test_multiple_sessions(self):
        """测试多个会话"""
        session_id1 = session_manager.create_session("alice")
        session_id2 = session_manager.create_session("bob")
        
        self.assertNotEqual(session_id1, session_id2)
        self.assertEqual(session_manager.get_session_count(), 2)
        
        # 验证会话独立
        session1 = session_manager.get_session(session_id1)
        session2 = session_manager.get_session(session_id2)
        
        self.assertEqual(session1['initiator'], "alice")
        self.assertEqual(session2['initiator'], "bob")


class CollaborationAPITestCase(TestCase):
    """REST API 测试"""
    
    def setUp(self):
        """测试前清理"""
        session_manager.active_sessions.clear()
    
    def test_create_session_api(self):
        """测试创建会话 API"""
        response = self.client.post(
            '/api/collaboration/sessions/create/',
            data={'initiator': 'alice'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('session_id', data)
    
    def test_get_session_api(self):
        """测试获取会话 API"""
        # 先创建会话
        session_id = session_manager.create_session("alice")
        
        response = self.client.get(
            f'/api/collaboration/sessions/{session_id}/'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['session']['initiator'], 'alice')
    
    def test_join_session_api(self):
        """测试加入会话 API"""
        session_id = session_manager.create_session("alice")
        
        response = self.client.post(
            f'/api/collaboration/sessions/{session_id}/join/',
            data={'member_id': 'bob', 'role': 'editor'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # 验证成员已添加
        members = session_manager.get_all_members(session_id)
        self.assertEqual(len(members), 2)
    
    def test_update_permission_api(self):
        """测试更新权限 API"""
        session_id = session_manager.create_session("alice")
        session_manager.add_member(session_id, "bob", role="viewer")
        
        response = self.client.post(
            f'/api/collaboration/sessions/{session_id}/permissions/',
            data={
                'initiator_id': 'alice',
                'member_id': 'bob',
                'role': 'editor'
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # 验证权限已更新
        role = session_manager.get_member_role(session_id, "bob")
        self.assertEqual(role, 'editor')
    
    def test_permission_denied_for_non_initiator(self):
        """测试非发起者无法修改权限"""
        session_id = session_manager.create_session("alice")
        session_manager.add_member(session_id, "bob", role="editor")
        session_manager.add_member(session_id, "charlie", role="viewer")
        
        # bob 尝试修改 charlie 的权限（应该失败）
        response = self.client.post(
            f'/api/collaboration/sessions/{session_id}/permissions/',
            data={
                'initiator_id': 'bob',
                'member_id': 'charlie',
                'role': 'editor'
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_session_stats_api(self):
        """测试统计信息 API"""
        session_manager.create_session("alice")
        session_manager.create_session("bob")
        
        response = self.client.get('/api/collaboration/stats/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['active_sessions'], 2)
