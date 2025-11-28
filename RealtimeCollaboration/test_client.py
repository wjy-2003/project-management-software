"""
Simple test client example
Demonstrates how to use the real-time collaboration API and WebSocket

Dependencies:
    pip install requests websocket-client

Usage:
    python test_client.py
"""
import requests
import json
import websocket
import time
from threading import Thread


class CollaborationClient:
    """Collaboration client wrapper"""
    
    def __init__(self, base_url="http://localhost:8000", ws_base_url="ws://localhost:8000"):
        self.base_url = base_url
        self.ws_base_url = ws_base_url
        self.session_id = None
        self.member_id = None
        self.ws = None
        
    def create_session(self, initiator_id):
        """Create a new session"""
        response = requests.post(
            f"{self.base_url}/api/collaboration/sessions/create/",
            json={"initiator": initiator_id}
        )
        data = response.json()
        if data['success']:
            self.session_id = data['session_id']
            self.member_id = initiator_id
            print(f"✓ Session created: {self.session_id}")
            return self.session_id
        else:
            print(f"✗ Failed to create session: {data['message']}")
            return None
    
    def join_session(self, session_id, member_id, role="viewer"):
        """Join an existing session"""
        response = requests.post(
            f"{self.base_url}/api/collaboration/sessions/{session_id}/join/",
            json={"member_id": member_id, "role": role}
        )
        data = response.json()
        if data['success']:
            self.session_id = session_id
            self.member_id = member_id
            print(f"✓ Joined session: {session_id} (role: {role})")
            return True
        else:
            print(f"✗ Failed to join session: {data['message']}")
            return False
    
    def get_session_info(self):
        """Get session information"""
        response = requests.get(
            f"{self.base_url}/api/collaboration/sessions/{self.session_id}/"
        )
        data = response.json()
        if data['success']:
            print(f"✓ Session info:")
            print(f"  Initiator: {data['session']['initiator']}")
            print(f"  Member count: {len(data['session']['members'])}")
            print(f"  Folders: {len(data['session']['structure']['folders'])}")
            print(f"  Files: {len(data['session']['structure']['files'])}")
            return data['session']
        else:
            print(f"✗ Failed to get session info: {data['message']}")
            return None
    
    def connect_websocket(self):
        """Connect to the WebSocket"""
        if not self.session_id or not self.member_id:
            print("✗ Please create or join a session first")
            return False
        
        ws_url = f"{self.ws_base_url}/ws/collaboration/{self.session_id}/{self.member_id}/"
        print(f"Connecting to WebSocket: {ws_url}")
        
        try:
            self.ws = websocket.create_connection(ws_url)
            print("✓ WebSocket connected")

            # Receive initial session info
            initial_msg = json.loads(self.ws.recv())
            if initial_msg['type'] == 'session_info':
                print(f"✓ Received session info")
            
            return True
        except Exception as e:
            print(f"✗ WebSocket connection failed: {e}")
            return False
    
    def create_folder(self, folder_id, folder_name, parent_id=None):
        """Create a folder"""
        if not self.ws:
            print("✗ WebSocket not connected")
            return False
        
        self.ws.send(json.dumps({
            "type": "structure_change",
            "operation": "create_folder",
            "payload": {
                "id": folder_id,
                "name": folder_name,
                "parent_id": parent_id
            }
        }))
        print(f"→ Sent create folder request: {folder_name}")
        return True
    
    def create_file(self, file_id, file_name, parent_id=None, file_type="text"):
        """Create a file"""
        if not self.ws:
            print("✗ WebSocket not connected")
            return False
        
        self.ws.send(json.dumps({
            "type": "structure_change",
            "operation": "create_file",
            "payload": {
                "id": file_id,
                "name": file_name,
                "parent_id": parent_id,
                "type": file_type
            }
        }))
        print(f"→ Sent create file request: {file_name}")
        return True
    
    def listen_messages(self, callback=None):
        """Listen for WebSocket messages"""
        if not self.ws:
            print("✗ WebSocket not connected")
            return
        
        print("Start listening for messages...")
        try:
            while True:
                message = json.loads(self.ws.recv())
                print(f"← Received message: {message['type']}")
                
                if callback:
                    callback(message)
                else:
                    self._default_message_handler(message)
                    
        except websocket.WebSocketConnectionClosedException:
            print("✗ WebSocket connection closed")
        except KeyboardInterrupt:
            print("\nStopped listening")
    
    def _default_message_handler(self, message):
        """Default message handler"""
        msg_type = message['type']
        
        if msg_type == 'structure_changed':
            operation = message['operation']
            payload = message['payload']
            print(f"  Structure change: {operation} - {payload}")
        
        elif msg_type == 'member_joined':
            print(f"  Member joined: {message['member_id']}")
        
        elif msg_type == 'member_left':
            print(f"  Member left: {message['member_id']}")
        
        elif msg_type == 'permission_updated':
            print(f"  Permission updated: {message['member_id']} → {message['new_role']}")
        
        elif msg_type == 'error':
            print(f"  Error: {message['message']}")
    
    def close(self):
        """Close the connection"""
        if self.ws:
            self.ws.close()
            print("✓ WebSocket disconnected")


def demo_basic_usage():
    # Create initiator client
    client1 = CollaborationClient()
    session_id = client1.create_session("alice")
    
    if not session_id:
        return
    
    # Connect to WebSocket
    if not client1.connect_websocket():
        return
    
    # Create folder structure
    client1.create_folder("f1", "src")
    time.sleep(0.5)
    
    client1.create_folder("f2", "utils", parent_id="f1")
    time.sleep(0.5)
    
    client1.create_file("file1", "main.py", parent_id="f1", file_type="python")
    time.sleep(0.5)
    
    # Get session information
    client1.get_session_info()
    
    # Listen for messages (blocking)
    print("\nListening for messages (press Ctrl+C to stop)...")
    try:
        client1.listen_messages()
    except KeyboardInterrupt:
        pass
    finally:
        client1.close()


def demo_multi_client():
    # Client 1: initiator
    client1 = CollaborationClient()
    session_id = client1.create_session("alice")
    
    if not session_id:
        return
    
    # Client 2: editor
    client2 = CollaborationClient()
    client2.join_session(session_id, "bob", role="editor")
    
    # Client 3: viewer (read-only)
    client3 = CollaborationClient()
    client3.join_session(session_id, "charlie", role="viewer")
    
    # Connect all clients
    if not all([
        client1.connect_websocket(),
        client2.connect_websocket(),
        client3.connect_websocket()
    ]):
        return
    
    # Client 1 creates a folder
    print("\n--- Alice creates folder ---")
    client1.create_folder("f1", "project")
    time.sleep(1)
    
    # Client 2 creates a file
    print("\n--- Bob creates file ---")
    client2.create_file("file1", "README.md", parent_id="f1", file_type="markdown")
    time.sleep(1)
    
    # Client 3 attempts to create a file (should fail, viewer role)
    print("\n--- Charlie attempts to create file (viewer) ---")
    client3.create_file("file2", "test.txt", parent_id="f1")
    time.sleep(1)
    
    # Check final session state
    print("\n--- Final session state ---")
    client1.get_session_info()
    
    # 清理
    client1.close()
    client2.close()
    client3.close()


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*50)
    print("Realtime Collaboration Test Client")
    print("="*50 + "\n")
    
    print("Select a test scenario:")
    print("1. Basic usage (single client)")
    print("2. Multi-client collaboration example")
    print("3. Exit")
    
    choice = input("\nEnter option (1-3): ").strip()
    
    if choice == "1":
        demo_basic_usage()
    elif choice == "2":
        demo_multi_client()
    elif choice == "3":
        print("Exit")
    else:
        print("Invalid option")
