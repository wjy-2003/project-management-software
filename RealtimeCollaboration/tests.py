# from django.test import TestCase

"""
Unit tests
"""
from django.test import TestCase
from .session_manager import session_manager


class SessionManagerTestCase(TestCase):
    """Session manager tests"""
    
    def setUp(self):
        """Clean up sessions before each test"""
        # Clear all sessions (for testing only)
        session_manager.active_sessions.clear()
    
    def test_create_session(self):
        """Test creating a session"""
        session_id = session_manager.create_session("alice")
        
        self.assertIsNotNone(session_id)
        self.assertTrue(session_manager.session_exists(session_id))
        
        session = session_manager.get_session(session_id)
        self.assertEqual(session['initiator'], "alice")
        self.assertIn("alice", session['members'])
    
    def test_add_member(self):
        """Test adding a member"""
        session_id = session_manager.create_session("alice")
        
        # test add editor
        success = session_manager.add_member(session_id, "bob", role="editor")
        self.assertTrue(success)
        
        # validation join members
        members = session_manager.get_all_members(session_id)
        self.assertEqual(len(members), 2)
        
        # check rules
        role = session_manager.get_member_role(session_id, "bob")
        self.assertEqual(role, "editor")
    
    def test_remove_member(self):
        """Test removing a member"""
        session_id = session_manager.create_session("alice")
        session_manager.add_member(session_id, "bob", role="editor")

        destroyed = session_manager.remove_member(session_id, "bob")
        self.assertFalse(destroyed)
        
        members = session_manager.get_all_members(session_id)
        self.assertEqual(len(members), 1)
    
    def test_session_destroyed_when_empty(self):
        """Test session is destroyed when last member leaves"""
        session_id = session_manager.create_session("alice")
        
        destroyed = session_manager.remove_member(session_id, "alice")
        self.assertTrue(destroyed)
        
        self.assertFalse(session_manager.session_exists(session_id))
    
    def test_permission_check(self):
        """Test permission checks"""
        session_id = session_manager.create_session("alice")
        session_manager.add_member(session_id, "bob", role="editor")
        session_manager.add_member(session_id, "charlie", role="viewer")
        
        self.assertTrue(session_manager.can_edit(session_id, "alice"))
        self.assertTrue(session_manager.can_edit(session_id, "bob"))
        self.assertFalse(session_manager.can_edit(session_id, "charlie"))
        
        self.assertTrue(session_manager.is_initiator(session_id, "alice"))
        self.assertFalse(session_manager.is_initiator(session_id, "bob"))
    
    def test_update_member_role(self):
        """Test updating a member's role"""
        session_id = session_manager.create_session("alice")
        session_manager.add_member(session_id, "bob", role="viewer")
        
        success = session_manager.update_member_role(session_id, "bob", "editor")
        self.assertTrue(success)
        
        role = session_manager.get_member_role(session_id, "bob")
        self.assertEqual(role, "editor")
    
    def test_cannot_update_initiator_role(self):
        """Test initiator role cannot be changed"""
        session_id = session_manager.create_session("alice")
        
        success = session_manager.update_member_role(session_id, "alice", "viewer")
        self.assertFalse(success)
    
    def test_structure_operations(self):
        """Test folder/file structure operations"""
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
        
        success = session_manager.update_structure(session_id, structure)
        self.assertTrue(success)
        
        updated_structure = session_manager.get_structure(session_id)
        self.assertEqual(len(updated_structure['folders']), 1)
        self.assertEqual(updated_structure['folders'][0]['name'], 'src')
    
    def test_multiple_sessions(self):
        """Test multiple sessions"""
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
    """REST API tests"""
    
    def setUp(self):
        """Clean up before tests"""
        session_manager.active_sessions.clear()
    
    def test_create_session_api(self):
        """Test create session API"""
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
        """Test get session API"""
        session_id = session_manager.create_session("alice")
        
        response = self.client.get(
            f'/api/collaboration/sessions/{session_id}/'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['session']['initiator'], 'alice')
    
    def test_join_session_api(self):
        """Test join session API"""
        session_id = session_manager.create_session("alice")
        
        response = self.client.post(
            f'/api/collaboration/sessions/{session_id}/join/',
            data={'member_id': 'bob', 'role': 'editor'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        members = session_manager.get_all_members(session_id)
        self.assertEqual(len(members), 2)
    
    def test_update_permission_api(self):
        """Test update permission API"""
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
        """Test non-initiator cannot change permissions"""
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
        """Test session stats API"""
        session_manager.create_session("alice")
        session_manager.create_session("bob")
        
        response = self.client.get('/api/collaboration/stats/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['active_sessions'], 2)
