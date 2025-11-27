// 测试前端API连接
import axios from 'axios';

// 后端配置
const BACKEND_IP = process.env.REACT_APP_BACKEND_IP || 'localhost';
const BACKEND_PORT = process.env.REACT_APP_BACKEND_PORT || '8001';
const API_BASE = process.env.REACT_APP_API_BASE || `http://${BACKEND_IP}:${BACKEND_PORT}/api/collaboration`;

console.log('🧪 测试前端API连接...');
console.log('🌐 后端地址:', API_BASE);

const testUserId = 'test_user_frontend_' + Date.now();

async function testCreateSession() {
  try {
    console.log('\n=== 测试创建会话 ===');
    console.log('请求地址:', `${API_BASE}/sessions/create/`);
    console.log('请求数据:', { initiator: testUserId });

    const response = await axios.post(`${API_BASE}/sessions/create/`, {
      initiator: testUserId
    });

    console.log('✅ 创建成功!');
    console.log('响应数据:', response.data);

    if (response.data.success && response.data.session_id) {
      console.log('📋 会话ID:', response.data.session_id);
      return response.data.session_id;
    } else {
      console.log('❌ 创建失败:', response.data);
      return null;
    }
  } catch (error) {
    console.error('❌ 创建错误:', error);
    console.error('错误详情:', error.response?.data);
    return null;
  }
}

async function testJoinSession(sessionId) {
  try {
    console.log('\n=== 测试加入会话 ===');
    console.log('请求地址:', `${API_BASE}/sessions/${sessionId}/join/`);

    const response = await axios.post(`${API_BASE}/sessions/${sessionId}/join/`, {
      member_id: testUserId + '_member',
      role: 'editor'
    });

    console.log('✅ 加入成功!');
    console.log('响应数据:', response.data);
    return true;
  } catch (error) {
    console.error('❌ 加入错误:', error);
    console.error('错误详情:', error.response?.data);
    return false;
  }
}

// 执行测试
(async () => {
  console.log('开始API测试...');

  const sessionId = await testCreateSession();

  if (sessionId) {
    await testJoinSession(sessionId);
  }

  console.log('\n=== 测试完成 ===');
  console.log('💡 如果测试通过，前端应该能正常工作');
})();
