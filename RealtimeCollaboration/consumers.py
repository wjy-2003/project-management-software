"""
Django Channels WebSocket Consumer
Handle WebSocket connections and messages for real-time collaboration
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
    Real-time collaborative WebSocket Consumer

    Handles functions such as session joining, message broadcasting, and structural changes.
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.member_id = self.scope['url_route']['kwargs']['member_id']
        self.group_name = f'collab_{self.session_id}'

        # validation
        session_exists = await sync_to_async(session_manager.session_exists)(
            self.session_id
        )
        
        if not session_exists:
            await self.close(code=4004)
            return

        # join a channel group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # update the member_channel
        await sync_to_async(session_manager.update_member_channel)(
            self.session_id,
            self.member_id,
            self.channel_name
        )

        # accept
        await self.accept()

        # update info to members
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

        # Notify other members that a new member has joined
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'member_joined',
                'member_id': self.member_id,
                'timestamp': datetime.now().isoformat()
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        session_destroyed = await sync_to_async(
            session_manager.remove_member
        )(self.session_id, self.member_id)

        # Notify other members that a member has left
        if not session_destroyed:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'member_left',
                    'member_id': self.member_id,
                    'timestamp': datetime.now().isoformat()
                }
            )

        # Leave the channel group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive messages from the WebSocket.
        Supports two modes:
        1. Yjs binary updates (bytes_data) - forward to other members
        2. JSON text messages (text_data) - used for structure changes, permissions, etc.
        """
        # Prioritize Yjs binary updates (usually Yjs CRDT updates)
        if bytes_data is not None:
            # Yjs sends raw binary data
            # Note: Channel Layer cannot transmit bytes directly; encode as base64
            encoded_update = base64.b64encode(bytes_data).decode('utf-8')
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'yjs_update',
                    'update': encoded_update,  # Pass base64-encoded string
                    'sender': self.member_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            return
        
        # Handle JSON text messages
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
        Handle requests to change folder/file structure.
        Changes from non-initiators must be approved by the initiator.
        """
        # Check if the member is the initiator
        is_initiator = await sync_to_async(
            session_manager.is_initiator
        )(self.session_id, self.member_id)

        # Check if the member has edit permission
        can_edit = await sync_to_async(
            session_manager.can_edit
        )(self.session_id, self.member_id)

        if not can_edit:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Permission denied: viewer role cannot edit structure',
                'timestamp': datetime.now().isoformat()
            }))
            return

        if not is_initiator:
            # Non-initiators must send a request to the initiator for approval
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

            # Send the change request to the initiator
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
            # Initiator applies the change directly
            await self.apply_structure_change(data)

    async def apply_structure_change(self, data):
        """
        Apply a structure change (called only by the initiator).
        """
        operation = data.get('operation')
        payload = data.get('payload')

        # Get the current structure
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

        # Modify the structure according to the operation type
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

            # Update the structure
            await sync_to_async(session_manager.update_structure)(
                self.session_id,
                structure
            )

            # Broadcast the change to all members
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
        Handle file content collaboration messages (e.g., Yjs instructions).
        Broadcast directly to all members without verification.
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
        Handle permission changes (only the initiator may call this).
        """
        # Verify if the member is the initiator
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

        # Update member role/permission
        success = await sync_to_async(
            session_manager.update_member_role
        )(self.session_id, target_member, new_role)

        if success:
            # Broadcast the permission change
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


    async def member_joined(self, event):
        """Notify that a member has joined"""
        if event['member_id'] != self.member_id:
            await self.send(text_data=json.dumps({
                'type': 'member_joined',
                'member_id': event['member_id'],
                'timestamp': event['timestamp']
            }))

    async def member_left(self, event):
        """Notify that a member has left"""
        await self.send(text_data=json.dumps({
            'type': 'member_left',
            'member_id': event['member_id'],
            'timestamp': event['timestamp']
        }))

    async def structure_change_request(self, event):
        """Forward structure change request (only to the initiator)"""
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
        """Broadcast structure changes"""
        await self.send(text_data=json.dumps({
            'type': 'structure_changed',
            'operation': event['operation'],
            'payload': event['payload'],
            'changed_by': event['changed_by'],
            'timestamp': event['timestamp']
        }))

    async def content_update(self, event):
        """Broadcast content updates"""
        # Do not send updates to the sender
        if event['sender'] != self.member_id:
            await self.send(text_data=json.dumps({
                'type': 'content_update',
                'file_id': event['file_id'],
                'content_data': event['content_data'],
                'sender': event['sender'],
                'timestamp': event['timestamp']
            }))

    async def permission_updated(self, event):
        """Broadcast permission updates"""
        await self.send(text_data=json.dumps({
            'type': 'permission_updated',
            'member_id': event['member_id'],
            'new_role': event['new_role'],
            'changed_by': event['changed_by'],
            'timestamp': event['timestamp']
        }))

    async def yjs_update(self, event):
        """
        Broadcast Yjs binary updates.
        Forward Yjs CRDT updates directly to other members (do not send back to sender).
        """
        # Do not send to the sender
        if event['sender'] != self.member_id:
            encoded_update = event.get('update')
            if encoded_update:
                # Decode the base64 string back to binary data
                binary_update = base64.b64decode(encoded_update)
                # Send binary data to the client
                await self.send(bytes_data=binary_update)
