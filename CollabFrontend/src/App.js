import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Tree, Button, List, message, Modal, Spin, Input, Dropdown, Menu, Tag, Alert } from 'antd';
import {
  FileTextOutlined, FolderOutlined, UserOutlined, PlusOutlined,
  LogoutOutlined, CopyOutlined, EditOutlined, DeleteOutlined,
  FolderAddOutlined, FileAddOutlined, TeamOutlined, CheckCircleOutlined
} from '@ant-design/icons';
import * as Y from 'yjs';
import axios from 'axios';
import './App.css';

// 从环境变量读取配置
const BACKEND_IP = process.env.REACT_APP_BACKEND_IP || 'localhost';
const BACKEND_PORT = process.env.REACT_APP_BACKEND_PORT || '8001';
const API_BASE = process.env.REACT_APP_API_BASE || `http://${BACKEND_IP}:${BACKEND_PORT}/api/collaboration`;
const WS_BASE = process.env.REACT_APP_WS_BASE || `ws://${BACKEND_IP}:${BACKEND_PORT}/ws/collaboration`;

// 简化的 Monaco 绑定
class SimpleBinding {
  constructor(ytext, monacoModel, onContentChange) {
    this.ytext = ytext;
    this.monacoModel = monacoModel;
    this.syncing = false;
    this.onContentChange = onContentChange;

    // 监听 Yjs 变化 -> 更新 Monaco
    this.observer = () => {
      if (this.syncing) return;
      this.syncing = true;

      const ytextContent = ytext.toString();
      const modelContent = monacoModel.getValue();

      if (ytextContent !== modelContent) {
        monacoModel.setValue(ytextContent);
      }

      this.syncing = false;
      if (this.onContentChange) {
        this.onContentChange(ytextContent);
      }
    };

    ytext.observe(this.observer);

    // 监听 Monaco 变化 -> 更新 Yjs
    this.changeDisposable = monacoModel.onDidChangeContent((event) => {
      if (this.syncing) return;
      this.syncing = true;

      // 使用事务来批量处理变化
      Y.transact(ytext.doc, () => {
        let offset = 0;
        event.changes.forEach(change => {
          const from = change.rangeOffset + offset;
          const to = from + change.rangeLength;

          if (change.text) {
            ytext.delete(from, to - from);
            ytext.insert(from, change.text);
          } else {
            ytext.delete(from, to - from);
          }

          offset += change.text.length - change.rangeLength;
        });
      });

      this.syncing = false;
    });

    // 初始同步
    const initialContent = ytext.toString();
    if (initialContent && initialContent !== monacoModel.getValue()) {
      monacoModel.setValue(initialContent);
    }
  }

  destroy() {
    if (this.ytext) {
      this.ytext.unobserve(this.observer);
    }
    if (this.changeDisposable) {
      this.changeDisposable.dispose();
    }
  }
}

function App() {
  const [sessionId, setSessionId] = useState('');
  const [userId] = useState(() => 'user_' + Math.random().toString(36).substr(2, 9));
  const [members, setMembers] = useState([]);
  const [structure, setStructure] = useState({ folders: [], files: [] });
  const [currentFile, setCurrentFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isInitiator, setIsInitiator] = useState(false);
  const [joinModalVisible, setJoinModalVisible] = useState(false);
  const [joinSessionId, setJoinSessionId] = useState('');
  const [createFileModalVisible, setCreateFileModalVisible] = useState(false);
  const [createFolderModalVisible, setCreateFolderModalVisible] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const [newFolderName, setNewFolderName] = useState('');
  const [shareSuccess, setShareSuccess] = useState(false);
  const [fileContents, setFileContents] = useState(new Map()); // 存储文件内容

  const wsRef = useRef(null);
  const ydocRef = useRef(null);
  const bindingRef = useRef(null);
  const editorRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // ==================== 创建房间 ====================
  const createSession = async () => {
    console.log('🚀 开始创建房间...');
    setLoading(true);
    try {
      console.log('创建会话请求:', `${API_BASE}/sessions/create/`);
      console.log('请求数据:', { initiator: userId });

      const response = await axios.post(`${API_BASE}/sessions/create/`, {
        initiator: userId
      });

      console.log('创建会话响应:', response.data);

      if (response.data.success) {
        const sessionId = response.data.session_id;
        setSessionId(sessionId);
        setIsInitiator(true);
        message.success('房间创建成功！');
        connectWebSocket(sessionId);

        // 自动创建示例文件
        setTimeout(() => {
          createExampleStructure(sessionId);
        }, 1000);
      } else {
        message.error(response.data.message || '创建失败');
      }
    } catch (error) {
      console.error('创建会话错误:', error);
      message.error(error.response?.data?.message || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建示例文件结构
  const createExampleStructure = (sessionId) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.log('WebSocket 未就绪，等待连接...');
      setTimeout(() => createExampleStructure(sessionId), 500);
      return;
    }

    console.log('开始创建示例文件结构...');
    const exampleFiles = [
      {
        operation: 'create_folder',
        payload: { id: 'folder_src', name: 'src', parent_id: null }
      },
      {
        operation: 'create_file',
        payload: { id: 'file_readme', name: 'README.md', parent_id: null, type: 'markdown' }
      },
      {
        operation: 'create_file',
        payload: { id: 'file_main', name: 'main.py', parent_id: 'folder_src', type: 'python' }
      },
      {
        operation: 'create_file',
        payload: { id: 'file_app', name: 'App.js', parent_id: 'folder_src', type: 'javascript' }
      }
    ];

    // 依次创建示例文件
    exampleFiles.forEach((file, index) => {
      setTimeout(() => {
        console.log('发送结构变更:', file);
        sendStructureChange(file);
      }, index * 500);
    });
  };

  // ==================== 加入房间 ====================
  const openJoinModal = () => {
    setJoinModalVisible(true);
    setJoinSessionId('');
  };

  const handleJoinSession = async () => {
    const id = joinSessionId.trim();
    if (!id) {
      message.error('请输入房间ID');
      return;
    }

    setLoading(true);
    try {
      console.log('加入会话请求:', `${API_BASE}/sessions/${id}/join/`);
      console.log('请求数据:', { member_id: userId, role: 'editor' });

      const response = await axios.post(`${API_BASE}/sessions/${id}/join/`, {
        member_id: userId,
        role: 'editor'
      });
      console.log('加入会话响应:', response.data);

      if (response.data.success) {
        setSessionId(id);
        setIsInitiator(false);
        message.success('加入成功！');
        setJoinModalVisible(false);
        connectWebSocket(id);
      } else {
        message.error(response.data.message || '加入失败');
      }
    } catch (error) {
      console.error('加入会话错误:', error);
      message.error(error.response?.data?.message || '加入失败');
    } finally {
      setLoading(false);
    }
  };

  // ==================== 退出房间 ====================
  const leaveSession = async () => {
    if (!sessionId) return;
    try {
      console.log('退出会话请求:', `${API_BASE}/sessions/${sessionId}/leave/`);
      await axios.post(`${API_BASE}/sessions/${sessionId}/leave/`, {
        member_id: userId
      });
      message.success('已退出房间');
    } catch (error) {
      console.error('退出错误:', error);
      message.warning('退出请求失败，本地已退出');
    } finally {
      // 清理资源与状态（无论后端是否成功）
      cleanupResources();
      setSessionId('');
      setMembers([]);
      setStructure({ folders: [], files: [] });
      setCurrentFile(null);
      setIsInitiator(false);
      setFileContents(new Map());
    }
  };

  const cleanupResources = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (ydocRef.current) {
      ydocRef.current.destroy();
      ydocRef.current = null;
    }
    if (bindingRef.current) {
      bindingRef.current.destroy();
      bindingRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
  };

  // ==================== WebSocket 连接 ====================
  const connectWebSocket = (sid) => {
    // 关闭现有连接
    cleanupResources();

    // 创建新的 Y.Doc
    ydocRef.current = new Y.Doc();

    const wsUrl = `${WS_BASE}/${sid}/${userId}/`;
    console.log('连接 WebSocket:', wsUrl);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        console.log('✅ WebSocket连接成功');
        message.success('实时协作已连接');
      };

      ws.onmessage = async (event) => {
        try {
          if (event.data instanceof ArrayBuffer) {
            // 处理 Yjs 二进制更新
            console.log('收到 Yjs 二进制更新');
            Y.applyUpdate(ydocRef.current, new Uint8Array(event.data));
          } else {
            // 处理 JSON 消息
            console.log('收到 WebSocket 消息:', event.data);
            const data = JSON.parse(event.data);
            await handleWebSocketMessage(data, sid);
          }
        } catch (error) {
          console.error('处理消息错误:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket连接关闭:', event);
        if (event.code !== 1000 && sessionId) {
          message.warning('连接已断开，尝试重连...');
          // 3秒后重连
          reconnectTimeoutRef.current = setTimeout(() => {
            if (sessionId) {
              connectWebSocket(sessionId);
            }
          }, 3000);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        message.error('连接错误');
      };

      // 监听 Yjs 更新并发送到服务器
      ydocRef.current.on('update', (update) => {
        if (ws.readyState === WebSocket.OPEN) {
          console.log('发送 Yjs 更新');
          ws.send(update);
        }
      });
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      message.error('WebSocket连接失败: ' + error.message);
    }
  };

  // ==================== 处理 WebSocket 消息 ====================
  const handleWebSocketMessage = async (data, sessionId) => {
    console.log('处理 WebSocket 消息:', data.type);

    switch (data.type) {
      case 'session_info':
        console.log('收到会话信息:', data.session);
        setMembers(data.session?.members || []);
        setStructure(data.session?.structure || { folders: [], files: [] });

        // 检查当前用户角色
        const currentMember = data.session?.members?.find(m => m.member_id === userId);
        const isInit = currentMember?.role === 'initiator';
        setIsInitiator(isInit);

        // 仅由创建者初始化默认文件内容，避免并发初始化导致内容拼接
        if (isInit) {
          initializeFileContents(data.session?.structure?.files || []);
        }
        break;

      case 'member_joined':
        console.log('成员加入:', data.member_id);
        await fetchMembers(sessionId);
        if (data.member_id !== userId) {
          message.info(`${data.member_id} 加入了房间`);
        }
        break;

      case 'member_left':
        console.log('成员离开:', data.member_id);
        await fetchMembers(sessionId);
        if (data.member_id !== userId) {
          message.info(`${data.member_id} 离开了房间`);
        }
        break;

      case 'structure_changed':
        console.log('结构变更:', data);
        await fetchStructure(sessionId);
        message.success('文件结构已更新');
        break;

      case 'structure_change_request':
        console.log('收到结构变更请求:', data);
        if (isInitiator) {
          Modal.confirm({
            title: '结构变更请求',
            content: `成员 ${data.requester} 请求: ${data.operation}`,
            okText: '同意',
            cancelText: '拒绝',
            onOk: () => {
              sendStructureChange({
                operation: data.operation,
                payload: data.payload
              });
            },
            onCancel: () => {
              message.info('已拒绝结构变更请求');
            }
          });
        }
        break;

      case 'error':
        console.error('服务器错误:', data.message);
        message.error(data.message);
        break;

      default:
        console.log('未知消息类型:', data.type);
    }
  };

  // 初始化文件内容
  const initializeFileContents = (files) => {
    const newFileContents = new Map();
    files.forEach(file => {
      if (!fileContents.has(file.id)) {
        const defaultContent = getDefaultContent(file.name, file.type);
        newFileContents.set(file.id, defaultContent);

        // 如果 Yjs 文档中还没有这个文件的内容，初始化它
        if (ydocRef.current) {
          const ytext = ydocRef.current.getText(file.id);
          if (ytext.length === 0) {
            ytext.insert(0, defaultContent);
          }
        }
      }
    });

    if (newFileContents.size > 0) {
      setFileContents(prev => new Map([...prev, ...newFileContents]));
    }
  };

  // ==================== 发送结构变更 ====================
  const sendStructureChange = (change) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message = {
        type: 'structure_change',
        ...change
      };
      console.log('发送结构变更:', message);
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket 连接未就绪');
      message.error('连接未就绪，请稍后重试');
    }
  };

  // ==================== API 调用 ====================
  const fetchStructure = async (sid) => {
    try {
      console.log('获取结构:', `${API_BASE}/sessions/${sid}/structure/`);
      const response = await axios.get(`${API_BASE}/sessions/${sid}/structure/`);
      setStructure(response.data.structure);
      console.log('结构数据:', response.data.structure);

      // 仅由创建者初始化默认文件内容（避免多人同时初始化导致冲突）
      if (isInitiator) {
        initializeFileContents(response.data.structure.files || []);
      }
    } catch (error) {
      console.error('获取结构失败:', error);
    }
  };

  const fetchMembers = async (sid) => {
    try {
      console.log('获取成员:', `${API_BASE}/sessions/${sid}/members/`);
      const response = await axios.get(`${API_BASE}/sessions/${sid}/members/`);
      setMembers(response.data.members);
      console.log('成员数据:', response.data.members);
    } catch (error) {
      console.error('获取成员失败:', error);
    }
  };

  // ==================== 文件操作 ====================
  const openCreateFileModal = () => {
    setCreateFileModalVisible(true);
    setNewFileName('');
  };

  const handleCreateFile = () => {
    if (!newFileName.trim()) {
      message.error('请输入文件名');
      return;
    }

    // 根据后缀推断类型
    let fileType = 'text';
    if (newFileName.endsWith('.js')) fileType = 'javascript';
    else if (newFileName.endsWith('.py')) fileType = 'python';
    else if (newFileName.endsWith('.html')) fileType = 'html';
    else if (newFileName.endsWith('.css')) fileType = 'css';
    else if (newFileName.endsWith('.md')) fileType = 'markdown';

    const fileId = 'file_' + Math.random().toString(36).substr(2, 9);

    console.log('创建文件:', { name: newFileName, type: fileType, id: fileId });

    sendStructureChange({
      operation: 'create_file',
      payload: {
        id: fileId,
        name: newFileName,
        parent_id: null,
        type: fileType
      }
    });

    setCreateFileModalVisible(false);
    setNewFileName('');
    message.success('文件创建请求已发送');
  };

  const openCreateFolderModal = () => {
    setCreateFolderModalVisible(true);
    setNewFolderName('');
  };

  const handleCreateFolder = () => {
    if (!newFolderName.trim()) {
      message.error('请输入文件夹名');
      return;
    }

    const folderId = 'folder_' + Math.random().toString(36).substr(2, 9);

    console.log('创建文件夹:', { name: newFolderName, id: folderId });

    sendStructureChange({
      operation: 'create_folder',
      payload: {
        id: folderId,
        name: newFolderName,
        parent_id: null
      }
    });

    setCreateFolderModalVisible(false);
    setNewFolderName('');
    message.success('文件夹创建请求已发送');
  };

  const renameFile = (file) => {
    let newName = file.name;

    Modal.confirm({
      title: '重命名文件',
      content: (
        <Input
          defaultValue={file.name}
          onChange={e => newName = e.target.value}
          onPressEnter={() => document.querySelector('.ant-modal-confirm-btns .ant-btn-primary').click()}
        />
      ),
      onOk: () => {
        if (!newName.trim()) {
          message.error('文件名不能为空');
          return;
        }

        sendStructureChange({
          operation: 'rename_file',
          payload: {
            id: file.id,
            new_name: newName
          }
        });
      }
    });
  };

  const renameFolder = (folder) => {
    let newName = folder.name;

    Modal.confirm({
      title: '重命名文件夹',
      content: (
        <Input
          defaultValue={folder.name}
          onChange={e => newName = e.target.value}
          onPressEnter={() => document.querySelector('.ant-modal-confirm-btns .ant-btn-primary').click()}
        />
      ),
      onOk: () => {
        if (!newName.trim()) {
          message.error('文件夹名不能为空');
          return;
        }

        sendStructureChange({
          operation: 'rename_folder',
          payload: {
            id: folder.id,
            new_name: newName
          }
        });
      }
    });
  };

  const deleteFile = (fileId) => {
    Modal.confirm({
      title: '删除文件',
      content: '确定要删除这个文件吗？此操作不可撤销。',
      okText: '删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: () => {
        sendStructureChange({
          operation: 'delete_file',
          payload: { id: fileId }
        });

        // 如果删除的是当前文件，关闭编辑器
        if (currentFile === fileId) {
          setCurrentFile(null);
        }

        // 从文件内容中移除
        setFileContents(prev => {
          const newContents = new Map(prev);
          newContents.delete(fileId);
          return newContents;
        });
      }
    });
  };

  const deleteFolder = (folderId) => {
    Modal.confirm({
      title: '删除文件夹',
      content: '确定要删除这个文件夹及其所有内容吗？此操作不可撤销。',
      okText: '删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: () => {
        sendStructureChange({
          operation: 'delete_folder',
          payload: { id: folderId }
        });
      }
    });
  };

  // ==================== 分享功能 ====================
  const shareLink = () => {
    const url = `${window.location.origin}${window.location.pathname}?room=${sessionId}`;
    console.log('分享链接:', url);

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(() => {
        setShareSuccess(true);
        message.success({
          content: (
            <div>
              <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
              链接已复制到剪贴板！
            </div>
          ),
          duration: 3,
        });

        // 3秒后隐藏成功提示
        setTimeout(() => setShareSuccess(false), 3000);
      }).catch((err) => {
        console.error('复制失败:', err);
        fallbackCopyText(url);
      });
    } else {
      fallbackCopyText(url);
    }
  };

  const fallbackCopyText = (text) => {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();

    try {
      const successful = document.execCommand('copy');
      if (successful) {
        setShareSuccess(true);
        message.success({
          content: (
            <div>
              <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
              链接已复制到剪贴板！
            </div>
          ),
          duration: 3,
        });
        setTimeout(() => setShareSuccess(false), 3000);
      } else {
        message.error('复制失败，请手动复制链接');
      }
    } catch (err) {
      console.error('复制失败:', err);
      message.error('复制失败，请手动复制链接');
    }

    document.body.removeChild(textArea);
  };

  // ==================== 文件树构建 ====================
  const buildTreeData = () => {
    const map = {};
    const roots = [];

    // 处理文件夹
    structure.folders?.forEach(f => {
      map[f.id] = {
        title: (
          <span>
            {f.name}
            {isInitiator && (
              <Dropdown
                menu={{
                  items: [
                    { key: 'add_file', icon: <FileAddOutlined />, label: '新建文件' },
                    { key: 'add_folder', icon: <FolderAddOutlined />, label: '新建文件夹' },
                    { key: 'rename', icon: <EditOutlined />, label: '重命名' },
                    { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true }
                  ],
                  onClick: ({ key }) => handleFolderMenu(key, f)
                }}
                trigger={['contextMenu']}
              >
                <span style={{ marginLeft: 8, color: '#999', cursor: 'pointer' }}>···</span>
              </Dropdown>
            )}
          </span>
        ),
        key: f.id,
        icon: <FolderOutlined />,
        children: [],
        isFolder: true,
        data: f
      };
    });

    // 处理文件
    structure.files?.forEach(f => {
      const node = {
        title: (
          <span>
            {f.name}
            {isInitiator && (
              <Dropdown
                menu={{
                  items: [
                    { key: 'rename', icon: <EditOutlined />, label: '重命名' },
                    { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true }
                  ],
                  onClick: ({ key }) => handleFileMenu(key, f)
                }}
                trigger={['contextMenu']}
              >
                <span style={{ marginLeft: 8, color: '#999', cursor: 'pointer' }}>···</span>
              </Dropdown>
            )}
          </span>
        ),
        key: f.id,
        icon: <FileTextOutlined />,
        isLeaf: true,
        data: f
      };

      if (f.parent_id && map[f.parent_id]) {
        map[f.parent_id].children.push(node);
      } else {
        roots.push(node);
      }
    });

    // 构建文件夹层级
    Object.values(map).forEach(folder => {
      if (folder.data.parent_id && map[folder.data.parent_id]) {
        map[folder.data.parent_id].children.push(folder);
      } else if (!folder.data.parent_id) {
        roots.push(folder);
      }
    });

    return roots;
  };

  const handleFolderMenu = (key, folder) => {
    console.log('文件夹菜单:', key, folder);
    switch (key) {
      case 'add_file':
        openCreateFileModal();
        break;
      case 'add_folder':
        openCreateFolderModal();
        break;
      case 'rename':
        renameFolder(folder);
        break;
      case 'delete':
        deleteFolder(folder.id);
        break;
    }
  };

  const handleFileMenu = (key, file) => {
    console.log('文件菜单:', key, file);
    switch (key) {
      case 'rename':
        renameFile(file);
        break;
      case 'delete':
        deleteFile(file.id);
        break;
    }
  };

  // ==================== 编辑器绑定 ====================
  const handleEditorDidMount = (editor, monaco) => {
    console.log('编辑器已挂载');
    editorRef.current = editor;

    if (currentFile) {
      initYjsBinding();
    }
  };

  const handleContentChange = (content) => {
    if (currentFile) {
      setFileContents(prev => new Map(prev.set(currentFile, content)));
    }
  };

  const initYjsBinding = () => {
    if (!currentFile || !ydocRef.current || !editorRef.current) {
      console.log('Yjs 绑定条件不满足');
      return;
    }

    console.log('初始化 Yjs 绑定 for file:', currentFile);

    // 清理旧的绑定
    if (bindingRef.current) {
      bindingRef.current.destroy();
    }

    const ytext = ydocRef.current.getText(currentFile);
    const model = editorRef.current.getModel();

    // 如果文件内容为空，设置默认内容
    if (ytext.length === 0) {
      const file = structure.files.find(f => f.id === currentFile);
      if (file) {
        const defaultContent = getDefaultContent(file.name, file.type);
        ytext.insert(0, defaultContent);
        console.log('设置默认内容:', defaultContent);
      }
    }

    bindingRef.current = new SimpleBinding(ytext, model, handleContentChange);
    console.log('Yjs 绑定初始化完成');
  };

  const getDefaultContent = (name, type) => {
    const contentMap = {
      markdown: `# ${name}\n\n欢迎使用实时协作编辑器！\n\n## 功能特性\n- 多人实时协作编辑\n- 支持多种编程语言\n- 实时同步文件结构\n\n开始与团队成员一起编辑吧！\n`,
      javascript: `// ${name}\n// 实时协作 JavaScript 文件\n\nconsole.log("欢迎使用实时协作编辑器！");\n\nfunction welcome() {\n    return "Hello, Collaborative Editor!";\n}\n\n// 开始编写你的代码...\n`,
      python: `# ${name}\n# 实时协作 Python 文件\n\nprint("欢迎使用实时协作编辑器！")\n\ndef main():\n    print("Hello, Collaborative Editor!")\n    return "协作编辑让编程更高效"\n\nif __name__ == "__main__":\n    main()\n`,
      html: `<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>${name}</title>\n    <style>\n        body {\n            font-family: Arial, sans-serif;\n            margin: 0;\n            padding: 20px;\n            background-color: #f5f5f5;\n        }\n        .container {\n            max-width: 800px;\n            margin: 0 auto;\n            background: white;\n            padding: 20px;\n            border-radius: 8px;\n            box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n        }\n    </style>\n</head>\n<body>\n    <div class="container">\n        <h1>欢迎使用实时协作编辑器</h1>\n        <p>这是一个协作编辑的 HTML 文件</p>\n        <p>多人可以同时编辑这个文件，所有更改都会实时同步</p>\n    </div>\n</body>\n</html>`,
      css: `/* ${name} */\n/* 实时协作 CSS 文件 */\n\n* {\n    margin: 0;\n    padding: 0;\n    box-sizing: border-box;\n}\n\nbody {\n    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\n    line-height: 1.6;\n    color: #333;\n    background-color: #f8f9fa;\n}\n\n.container {\n    max-width: 1200px;\n    margin: 0 auto;\n    padding: 20px;\n}\n\n.header {\n    background: white;\n    padding: 1rem 2rem;\n    border-bottom: 1px solid #e1e5e9;\n    box-shadow: 0 2px 4px rgba(0,0,0,0.1);\n}\n\n/* 开始编写你的样式... */\n`
    };
    return contentMap[type] || `# ${name}\n\n这是一个文本文件。\n\n开始与团队成员一起编辑吧！\n`;
  };

  // 当文件改变时重新初始化绑定
  useEffect(() => {
    if (currentFile && editorRef.current) {
      console.log('当前文件改变:', currentFile);
      initYjsBinding();
    }
  }, [currentFile]);

  // 清理函数
  useEffect(() => {
    return () => {
      console.log('清理资源');
      cleanupResources();
    };
  }, []);

  // URL 自动加入
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const room = params.get('room');
    if (room && !sessionId) {
      console.log('自动加入房间:', room);
      setSessionId(room);
      // 延迟执行加入操作
      setTimeout(() => {
        axios.post(`${API_BASE}/sessions/${room}/join/`, {
          member_id: userId,
          role: 'editor'
        })
        .then(() => {
          connectWebSocket(room);
          message.success('已自动加入房间');
        })
        .catch(err => {
          console.error('自动加入失败:', err);
          message.error('自动加入房间失败');
        });
      }, 100);
    }
  }, []);

  return (
    <div className="app">
      <header className="header">
        <h2>🚀 实时协作编辑器</h2>
        <div className="header-right">
          {sessionId ? (
            <>
              <Tag color="blue">
                <TeamOutlined /> 房间: {sessionId.slice(0, 8)}...
              </Tag>

              {/* 分享成功提示 */}
              {shareSuccess && (
                <Alert
                  message="链接已复制！"
                  description="现在可以将链接分享给其他人一起协作了"
                  type="success"
                  showIcon
                  style={{ marginRight: 16, maxWidth: 300 }}
                />
              )}

              <Button
                icon={<CopyOutlined />}
                onClick={shareLink}
                style={{ margin: '0 8px' }}
                type={shareSuccess ? "default" : "primary"}
              >
                {shareSuccess ? "已复制" : "分享"}
              </Button>
              <Button
                danger
                icon={<LogoutOutlined />}
                onClick={leaveSession}
              >
                退出
              </Button>
            </>
          ) : (
            <>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={createSession}
                loading={loading}
                style={{ margin: '0 8px' }}
              >
                创建房间
              </Button>
              <Button
                onClick={openJoinModal}
                loading={loading}
              >
                加入房间
              </Button>
            </>
          )}
        </div>
      </header>

      {/* 加入会话模态框 */}
      <Modal
        title="加入房间"
        open={joinModalVisible}
        onOk={handleJoinSession}
        onCancel={() => setJoinModalVisible(false)}
        confirmLoading={loading}
        okText="加入"
        cancelText="取消"
      >
        <div>
          <p>请输入要加入的房间ID:</p>
          <Input
            placeholder="房间ID"
            value={joinSessionId}
            onChange={e => setJoinSessionId(e.target.value)}
            onPressEnter={handleJoinSession}
          />
          <p style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            提示：向房间创建者获取房间ID
          </p>
        </div>
      </Modal>

      {/* 创建文件模态框 */}
      <Modal
        title="新建文件"
        open={createFileModalVisible}
        onOk={handleCreateFile}
        onCancel={() => setCreateFileModalVisible(false)}
        okText="创建"
        cancelText="取消"
      >
        <div>
          <p>请输入文件名:</p>
          <Input
            placeholder="文件名（如：main.py）"
            value={newFileName}
            onChange={e => setNewFileName(e.target.value)}
            onPressEnter={handleCreateFile}
          />
          <p style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            提示：文件名包含后缀，如 .py、.js、.md 等
          </p>
        </div>
      </Modal>

      {/* 创建文件夹模态框 */}
      <Modal
        title="新建文件夹"
        open={createFolderModalVisible}
        onOk={handleCreateFolder}
        onCancel={() => setCreateFolderModalVisible(false)}
        okText="创建"
        cancelText="取消"
      >
        <div>
          <p>请输入文件夹名:</p>
          <Input
            placeholder="文件夹名"
            value={newFolderName}
            onChange={e => setNewFolderName(e.target.value)}
            onPressEnter={handleCreateFolder}
          />
        </div>
      </Modal>

      {sessionId ? (
        <div className="main-layout">
          {/* 左侧文件树 */}
          <div className="sidebar left">
            <div className="sidebar-header">
              <h3>
                📁 文件浏览器
                {isInitiator && <Tag color="gold" style={{ marginLeft: 8 }}>创建者</Tag>}
              </h3>
            </div>
            {isInitiator && (
              <div style={{ padding: 8, borderBottom: '1px solid #f0f0f0' }}>
                <Button
                  size="small"
                  block
                  icon={<FileAddOutlined />}
                  onClick={openCreateFileModal}
                >
                  新建文件
                </Button>
                <Button
                  size="small"
                  block
                  style={{ marginTop: 4 }}
                  icon={<FolderAddOutlined />}
                  onClick={openCreateFolderModal}
                >
                  新建文件夹
                </Button>
              </div>
            )}
            <div className="tree-container">
              <Tree
                treeData={buildTreeData()}
                defaultExpandAll
                onSelect={([key]) => {
                  console.log('选择文件:', key);
                  if (key) {
                    const file = structure.files?.find(f => f.id === key);
                    if (file) {
                      setCurrentFile(key);
                    }
                  }
                }}
                selectedKeys={[currentFile]}
                blockNode
                showIcon
              />
            </div>
          </div>

          {/* 中间编辑器 */}
          <div className="editor-container">
            {currentFile ? (
              <>
                <div className="editor-header">
                  <FileTextOutlined />
                  <span style={{ marginLeft: 8 }}>
                    {structure.files.find(f => f.id === currentFile)?.name}
                  </span>
                  <Tag style={{ marginLeft: 8 }}>
                    {structure.files.find(f => f.id === currentFile)?.type}
                  </Tag>
                  <span style={{ marginLeft: 'auto', fontSize: 12, color: '#666' }}>
                    实时同步中...
                  </span>
                </div>
                <Editor
                  height="calc(100% - 40px)"
                  language={structure.files.find(f => f.id === currentFile)?.type || 'text'}
                  theme="vs-dark"
                  onMount={handleEditorDidMount}
                  options={{
                    fontSize: 14,
                    wordWrap: 'on',
                    minimap: { enabled: true },
                    automaticLayout: true,
                    readOnly: !isInitiator && members.find(m => m.member_id === userId)?.role === 'viewer'
                  }}
                />
              </>
            ) : (
              <div className="placeholder">
                <FileTextOutlined style={{ fontSize: 64, color: '#ddd', marginBottom: 16 }} />
                <p>选择一个文件开始编辑</p>
                <p style={{ color: '#999', fontSize: 12 }}>支持多人实时协作编辑</p>
                {members.length > 1 && (
                  <p style={{ color: '#52c41a', fontSize: 12, marginTop: 8 }}>
                    👥 {members.length} 人正在协作
                  </p>
                )}
              </div>
            )}
          </div>

          {/* 右侧成员列表 */}
          <div className="sidebar right">
            <div className="sidebar-header">
              <h3>👥 在线成员 ({members.length})</h3>
            </div>
            <div className="members-list">
              <List
                dataSource={members}
                renderItem={member => (
                  <List.Item>
                    <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <UserOutlined
                        style={{
                          color: member.role === 'initiator' ? '#faad14' : '#52c41a'
                        }}
                      />
                      <span style={{ marginLeft: 8, flex: 1 }}>
                        {member.member_id}
                        {member.member_id === userId && (
                          <Tag color="purple" size="small" style={{ marginLeft: 4 }}>我</Tag>
                        )}
                      </span>
                      <Tag
                        size="small"
                        color={member.role === 'initiator' ? 'gold' : 'green'}
                      >
                        {member.role}
                      </Tag>
                    </div>
                  </List.Item>
                )}
                size="small"
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="welcome">
          <div className="welcome-content">
            <Spin spinning={loading} size="large" />
            <h3 style={{ marginTop: 32, marginBottom: 16 }}>欢迎使用实时协作编辑器</h3>
            <p style={{ color: '#666', textAlign: 'center' }}>
              创建新房间或加入现有房间开始协作编辑
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
