"""
Django Channels WebSocket Consumer
处理实时协作的 WebSocket 连接和消息
"""
import json
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
from typing import Optional
from asgiref.sync import sync_to_async

from .session_manager import session_manager


class CollaborationConsumer(AsyncWebsocketConsumer):
    """
    实时协作 WebSocket Consumer
    处理会话加入、消息广播、结构变更等功能
    """

    async def connect(self):
        """处理 WebSocket 连接"""
        # 从 URL 路径获取会话 ID 和成员 ID
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.member_id = self.scope['url_route']['kwargs']['member_id']
        self.group_name = f'collab_{self.session_id}'

        # 验证会话是否存在
        session_exists = await sync_to_async(session_manager.session_exists)(
            self.session_id
        )
        
        if not session_exists:
            await self.close(code=4004)
            return

        # 加入频道组
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # 更新成员的通道名称
        await sync_to_async(session_manager.update_member_channel)(
            self.session_id,
            self.member_id,
            self.channel_name
        )

        # 接受 WebSocket 连接
        await self.accept()

        # 获取当前会话信息并发送给新连接的成员
        session = await sync_to_async(session_manager.get_session)(
            self.session_id
        )
        
        if session:
            await self.send(text_data=json.dumps({
                'type': 'session_info',
                'session': {
                    'session_id': session['session_id'],
                    'initiator': session['initiator'],
                    'members': await sync_to_async(
                        session_manager.get_all_members
                    )(self.session_id),
                    'structure': session['structure']
                },
                'timestamp': datetime.now().isoformat()
            }))

        # 通知其他成员有新成员加入
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'member_joined',
                'member_id': self.member_id,
                'timestamp': datetime.now().isoformat()
            }
        )

    async def disconnect(self, close_code):
        """处理 WebSocket 断开连接"""
        # 从会话中移除成员
        session_destroyed = await sync_to_async(
            session_manager.remove_member
        )(self.session_id, self.member_id)

        # 通知其他成员有成员离开
        if not session_destroyed:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'member_left',
                    'member_id': self.member_id,
                    'timestamp': datetime.now().isoformat()
                }
            )

        # 离开频道组
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """
        接收来自 WebSocket 的消息
        支持两种模式：
        1. Yjs 二进制更新（bytes_data）- 直接广播给其他成员
        2. JSON 文本消息（text_data）- 用于结构变更、权限管理等
        """
        # 优先处理 Yjs 二进制更新（通常是 Yjs 的 CRDT 更新）
        if bytes_data is not None:
            # Yjs 发送的是纯二进制数据
            # 注意：Channel Layer 不能直接传递 bytes，需要编码为 base64
            encoded_update = base64.b64encode(bytes_data).decode('utf-8')
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'yjs_update',
                    'update': encoded_update,  # 传递 base64 编码的字符串
                    'sender': self.member_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            return
        
        # 处理 JSON 文本消息
        if text_data is None:
            return
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'structure_change':
                await self.handle_structure_change(data)
            elif message_type == 'content_collaboration':
                await self.handle_content_collaboration(data)
            elif message_type == 'permission_change':
                await self.handle_permission_change(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}',
                    'timestamp': datetime.now().isoformat()
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format',
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }))

    async def handle_structure_change(self, data):
        """
        处理文件夹结构变更请求
        非发起者的变更需要发起者验证
        """
        # 检查是否为发起者
        is_initiator = await sync_to_async(
            session_manager.is_initiator
        )(self.session_id, self.member_id)

        # 检查是否有编辑权限
        can_edit = await sync_to_async(
            session_manager.can_edit
        )(self.session_id, self.member_id)

        if not can_edit:
            # 只读成员无权修改
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Permission denied: viewer role cannot edit structure',
                'timestamp': datetime.now().isoformat()
            }))
            return

        if not is_initiator:
            # 非发起者需要发送请求给发起者验证
            session = await sync_to_async(
                session_manager.get_session
            )(self.session_id)
            
            if not session:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Session not found',
                    'timestamp': datetime.now().isoformat()
                }))
                return

            # 发送变更请求给发起者
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'structure_change_request',
                    'requester': self.member_id,
                    'operation': data.get('operation'),
                    'payload': data.get('payload'),
                    'timestamp': datetime.now().isoformat()
                }
            )
        else:
            # 发起者直接应用变更
            await self.apply_structure_change(data)

    async def apply_structure_change(self, data):
        """
        应用结构变更（仅发起者调用）
        """
        operation = data.get('operation')
        payload = data.get('payload')

        # 获取当前结构
        structure = await sync_to_async(
            session_manager.get_structure
        )(self.session_id)

        if not structure:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Session structure not found',
                'timestamp': datetime.now().isoformat()
            }))
            return

        # 根据操作类型修改结构
        try:
            if operation == 'create_folder':
                structure['folders'].append({
                    'id': payload['id'],
                    'name': payload['name'],
                    'parent_id': payload.get('parent_id')
                })
            elif operation == 'create_file':
                structure['files'].append({
                    'id': payload['id'],
                    'name': payload['name'],
                    'parent_id': payload.get('parent_id'),
                    'type': payload.get('type', 'text')
                })
            elif operation == 'delete_folder':
                structure['folders'] = [
                    f for f in structure['folders'] 
                    if f['id'] != payload['id']
                ]
            elif operation == 'delete_file':
                structure['files'] = [
                    f for f in structure['files'] 
                    if f['id'] != payload['id']
                ]
            elif operation == 'move_folder':
                for folder in structure['folders']:
                    if folder['id'] == payload['id']:
                        folder['parent_id'] = payload['new_parent_id']
                        break
            elif operation == 'move_file':
                for file in structure['files']:
                    if file['id'] == payload['id']:
                        file['parent_id'] = payload['new_parent_id']
                        break
            elif operation == 'rename_folder':
                for folder in structure['folders']:
                    if folder['id'] == payload['id']:
                        folder['name'] = payload['new_name']
                        break
            elif operation == 'rename_file':
                for file in structure['files']:
                    if file['id'] == payload['id']:
                        file['name'] = payload['new_name']
                        break
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown operation: {operation}',
                    'timestamp': datetime.now().isoformat()
                }))
                return

            # 更新结构
            await sync_to_async(session_manager.update_structure)(
                self.session_id,
                structure
            )

            # 广播变更给所有成员
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'structure_changed',
                    'operation': operation,
                    'payload': payload,
                    'changed_by': self.member_id,
                    'timestamp': datetime.now().isoformat()
                }
            )

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error applying structure change: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }))

    async def handle_content_collaboration(self, data):
        """
        处理文件内容协作消息（如 Yjs 指令）
        直接广播给所有成员，无需验证
        """
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'content_update',
                'file_id': data.get('file_id'),
                'content_data': data.get('content_data'),
                'sender': self.member_id,
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_permission_change(self, data):
        """
        处理权限变更（仅发起者可调用）
        """
        # 验证是否为发起者
        is_initiator = await sync_to_async(
            session_manager.is_initiator
        )(self.session_id, self.member_id)

        if not is_initiator:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Permission denied: only initiator can change permissions',
                'timestamp': datetime.now().isoformat()
            }))
            return

        target_member = data.get('member_id')
        new_role = data.get('role')

        if new_role not in ['editor', 'viewer']:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid role: must be "editor" or "viewer"',
                'timestamp': datetime.now().isoformat()
            }))
            return

        # 更新权限
        success = await sync_to_async(
            session_manager.update_member_role
        )(self.session_id, target_member, new_role)

        if success:
            # 广播权限变更
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'permission_updated',
                    'member_id': target_member,
                    'new_role': new_role,
                    'changed_by': self.member_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to update permission',
                'timestamp': datetime.now().isoformat()
            }))

    # 以下是频道层消息处理方法

    async def member_joined(self, event):
        """通知成员加入"""
        if event['member_id'] != self.member_id:
            await self.send(text_data=json.dumps({
                'type': 'member_joined',
                'member_id': event['member_id'],
                'timestamp': event['timestamp']
            }))

    async def member_left(self, event):
        """通知成员离开"""
        await self.send(text_data=json.dumps({
            'type': 'member_left',
            'member_id': event['member_id'],
            'timestamp': event['timestamp']
        }))

    async def structure_change_request(self, event):
        """转发结构变更请求（仅发给发起者）"""
        is_initiator = await sync_to_async(
            session_manager.is_initiator
        )(self.session_id, self.member_id)

        if is_initiator:
            await self.send(text_data=json.dumps({
                'type': 'structure_change_request',
                'requester': event['requester'],
                'operation': event['operation'],
                'payload': event['payload'],
                'timestamp': event['timestamp']
            }))

    async def structure_changed(self, event):
        """广播结构变更"""
        await self.send(text_data=json.dumps({
            'type': 'structure_changed',
            'operation': event['operation'],
            'payload': event['payload'],
            'changed_by': event['changed_by'],
            'timestamp': event['timestamp']
        }))

    async def content_update(self, event):
        """广播内容更新"""
        # 不发送给自己
        if event['sender'] != self.member_id:
            await self.send(text_data=json.dumps({
                'type': 'content_update',
                'file_id': event['file_id'],
                'content_data': event['content_data'],
                'sender': event['sender'],
                'timestamp': event['timestamp']
            }))

    async def permission_updated(self, event):
        """广播权限更新"""
        await self.send(text_data=json.dumps({
            'type': 'permission_updated',
            'member_id': event['member_id'],
            'new_role': event['new_role'],
            'changed_by': event['changed_by'],
            'timestamp': event['timestamp']
        }))

    async def yjs_update(self, event):
        """
        广播 Yjs 二进制更新
        将 Yjs CRDT 更新直接转发给其他成员（不发送给自己）
        """
        # 不发送给自己
        if event['sender'] != self.member_id:
            encoded_update = event.get('update')
            if encoded_update:
                # 将 base64 字符串解码回二进制数据
                binary_update = base64.b64decode(encoded_update)
                # 发送二进制数据给客户端
                await self.send(bytes_data=binary_update)
