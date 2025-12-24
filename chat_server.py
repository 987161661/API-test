"""
WebSocket 实时群聊后台服务

运行方式:
    uvicorn chat_server:app --host 0.0.0.0 --port 8000 --reload

功能:
    - WebSocket 端点支持实时双向通信
    - 持续运行对话循环
    - 用户可随时插入消息
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Dict, List, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入现有的意识探针模块
import sys
import os

# 确保能找到 core 目录
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from core.consciousness import ConsciousnessProbe, ConsciousnessGroupSession
    from core.base import LLMProvider
    from providers.openai_compatible import OpenAICompatibleProvider
except ImportError as e:
    # 如果导入失败，可能是因为路径问题或者依赖缺失
    # 我们不应该隐藏这个错误，否则后续代码会崩溃
    print(f"Critical Import Error: {e}")
    print(f"sys.path: {sys.path}")
    raise e

app = FastAPI(title="AI Group Chat WebSocket Server")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRoom:
    """群聊房间管理"""
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.clients: Set[WebSocket] = set()
        self.history: List[Dict] = []
        self.probes: List[ConsciousnessProbe] = []
        self.session: Optional[ConsciousnessGroupSession] = None
        self.is_running = False
        self.model_tasks: List[asyncio.Task] = []
        self.stop_event: Optional[asyncio.Event] = None
        self.typing_users: Set[str] = set()
        
        # 新增属性：群信息和成员配置
        self.group_name = "语言模型内部意识讨论群"
        self.member_configs: Dict[str, dict] = {} # model_name -> {is_manager: bool, custom_prompt: str}

    async def connect(self, websocket: WebSocket):
        """新客户端连接"""
        await websocket.accept()
        self.clients.add(websocket)
        
        # 发送历史消息
        await websocket.send_json({
            "type": "history",
            "messages": self.history
        })
        
        # 发送状态
        await websocket.send_json({
            "type": "status",
            "is_running": self.is_running,
            "member_count": len(self.probes) + 1
        })
    
    def disconnect(self, websocket: WebSocket):
        """客户端断开"""
        self.clients.discard(websocket)
    
    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        disconnected = set()
        for client in self.clients:
            try:
                await client.send_json(message)
            except:
                disconnected.add(client)
        
        # 清理断开的连接
        self.clients -= disconnected
    
    async def add_message(self, name: str, content: str, is_user: bool = False):
        """添加消息并广播"""
        now = datetime.now()
        msg = {
            "name": name,
            "content": content,
            "timestamp": now.strftime("%H:%M:%S"),
            "ts": now.timestamp(), # Unix timestamp for calculations
            "is_user": is_user
        }
        
        # Inject avatar if available
        if name in self.member_configs and "avatar" in self.member_configs[name]:
            msg["avatar"] = self.member_configs[name]["avatar"]
        elif is_user:
            # Default Gaia avatar if not provided? Or client handles it.
            pass

        self.history.append(msg)
        
        await self.broadcast({
            "type": "message",
            "message": msg
        })
    
    async def update_typing_status(self, model_name: str, is_typing: bool):
        """更新单个模型的输入状态并广播"""
        if is_typing:
            self.typing_users.add(model_name)
        else:
            self.typing_users.discard(model_name)
            
        await self.broadcast({
            "type": "typing",
            "models": list(self.typing_users)
        })

    async def set_typing(self, models: List[str]):
        """设置正在输入状态 (Legacy/Batch)"""
        self.typing_users = set(models)
        await self.broadcast({
            "type": "typing",
            "models": list(self.typing_users)
        })
    
    async def send_thought(self, model_name: str, content: str):
        """发送思考内容到所有客户端"""
        await self.broadcast({
            "type": "thought",
            "model": model_name,
            "content": content
        })

    def setup_probes(self, model_configs: List[dict]):
        """设置模型探针"""
        self.probes = []
        
        for config in model_configs:
            m_name = config.get("model_name", "gpt-4")
            
            # Store initial configs if provided
            if m_name not in self.member_configs:
                self.member_configs[m_name] = {
                    "is_manager": config.get("is_manager", False),
                    "custom_prompt": config.get("custom_prompt", "")
                }
            
            provider = OpenAICompatibleProvider(
                api_key=config.get("api_key", ""),
                base_url=config.get("base_url", "")
            )
            
            # 创建回调函数来广播思考过程
            def create_log_callback(name):
                def callback(msg):
                    # 由于 callback 是同步调用的，我们需要用 asyncio.create_task 发送异步消息
                    # 但在多线程/协程环境下，我们需要确保在正确的事件循环中运行
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(self.send_thought(name, msg), loop)
                    except Exception as e:
                        print(f"Error in thought callback: {e}")
                return callback

            probe = ConsciousnessProbe(
                provider=provider,
                model_name=m_name,
                config={"temperature": 0.85, "max_tokens": 512},
                log_callback=create_log_callback(m_name)
            )
            self.probes.append(probe)
        
        # 将 log_callback 传递给 session
        def group_log(msg):
            try:
                loop = asyncio.get_event_loop()
                # Ensure msg is string and strip it for comparison
                msg_str = str(msg).strip()
                if msg_str == "NEW_MESSAGE":
                    # 获取最新的一条消息并广播
                    if self.history:
                        latest_msg = self.history[-1]
                        # 补全消息字段 (Modifies the dict in self.history in-place)
                        if "timestamp" not in latest_msg:
                            latest_msg["timestamp"] = datetime.now().strftime("%H:%M:%S")
                        if "is_user" not in latest_msg:
                            latest_msg["is_user"] = False
                            
                        # 广播标准消息格式
                        asyncio.run_coroutine_threadsafe(self.broadcast({
                            "type": "message",
                            "message": latest_msg
                        }), loop)
                else:
                    asyncio.run_coroutine_threadsafe(self.broadcast({"type": "system", "content": msg}), loop)
            except Exception as e:
                print(f"Error in group_log: {e}")

        self.session = ConsciousnessGroupSession(
            self.probes, 
            log_callback=group_log,
            group_name=self.group_name,
            member_configs=self.member_configs
        )
    
    def start_chat(self):
        """启动群聊循环 (Autonomous Agents Mode)"""
        if not self.is_running and self.probes and self.session:
            self.is_running = True
            self.stop_event = asyncio.Event()
            self.model_tasks = []
            
            # Callback for typing status
            async def on_typing(model_name, is_typing):
                # Ensure we run this on the main loop
                try:
                    await self.update_typing_status(model_name, is_typing)
                except Exception as e:
                    print(f"Typing callback error: {e}")

            # Start a task for each probe
            for probe in self.probes:
                task = asyncio.create_task(
                    self.session.run_autonomous_loop(
                        probe=probe,
                        history_manager=self.history,
                        stop_event=self.stop_event,
                        typing_callback=on_typing
                    )
                )
                self.model_tasks.append(task)
            
            # Broadcast status update (need to wrap in task if not async)
            asyncio.create_task(self.broadcast({"type": "status", "is_running": True}))
            
    async def stop_chat(self):
        """停止群聊循环"""
        self.is_running = False
        
        if self.stop_event:
            self.stop_event.set()
        
        if self.model_tasks:
            for task in self.model_tasks:
                task.cancel()
            
            # Wait for all tasks to finish/cancel
            await asyncio.gather(*self.model_tasks, return_exceptions=True)
            self.model_tasks = []
            
        await self.broadcast({"type": "status", "is_running": False})


# 全局房间管理
rooms: Dict[str, ChatRoom] = {}


def get_or_create_room(room_id: str) -> ChatRoom:
    """获取或创建房间"""
    if room_id not in rooms:
        rooms[room_id] = ChatRoom(room_id)
    return rooms[room_id]


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket 端点"""
    room = get_or_create_room(room_id)
    await room.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            try:
                if data["type"] == "user_message":
                    # 用户发送消息
                    await room.add_message(
                        name=data.get("name", "Gaia"),
                        content=data["content"],
                        is_user=True
                    )
                    # 如果收到用户消息后没在运行，自动点火
                    if not room.is_running:
                        room.start_chat()
                
                elif data["type"] == "setup":
                    # 设置模型配置
                    # Update group name if provided
                    if "group_name" in data:
                        room.group_name = data["group_name"]
                        
                    # Update member configs if provided in models list
                    if "models" in data:
                        # Clear existing configs if full update
                        # room.member_configs = {} 
                        for m_conf in data["models"]:
                            m_name = m_conf.get("model_name")
                            if m_name:
                                room.member_configs[m_name] = {
                                    "is_manager": m_conf.get("is_manager", False),
                                    "custom_prompt": m_conf.get("custom_prompt", ""),
                                    "avatar": m_conf.get("avatar", "")
                                }
                        room.setup_probes(data["models"])

                    # Feature 1: DO NOT auto start chat
                    # if not room.is_running:
                    #    room.start_chat()
                    
                    await websocket.send_json({
                        "type": "status",
                        "is_running": room.is_running,
                        "member_count": len(room.probes) + 1,
                        "group_info": {
                            "name": room.group_name
                        }
                    })
                
                elif data["type"] == "update_settings":
                    # Just update settings without full reset
                    if "group_name" in data:
                        room.group_name = data["group_name"]
                    
                    if "member_configs" in data:
                        # Expect dict: {model_name: {is_manager: bool, custom_prompt: str}}
                        for m_name, conf in data["member_configs"].items():
                            if m_name in room.member_configs:
                                room.member_configs[m_name].update(conf)
                                
                    # Refresh session with new settings
                    if room.session:
                        room.session.group_name = room.group_name
                        room.session.member_configs = room.member_configs
                    
                    # Broadcast update to all clients
                    await room.broadcast({
                        "type": "settings_updated",
                        "group_name": room.group_name,
                        "member_configs": room.member_configs
                    })

                elif data["type"] == "start":
                    # 启动对话循环
                    room.start_chat()
                
                elif data["type"] == "stop":
                    # 停止对话循环
                    await room.stop_chat()
                
                elif data["type"] == "clear":
                    # 清空历史
                    room.history = []
                    await room.broadcast({"type": "history", "messages": []})
                
                elif data["type"] == "reset":
                    # 停止并清空
                    await room.stop_chat()
                    room.history = []
                    await room.broadcast({"type": "history", "messages": []})
                
                elif data["type"] == "get_members":
                    # 获取当前成员列表
                    members = [{"name": "Gaia", "is_user": True, "is_manager": True}] # User is always manager-like
                    for p in room.probes:
                        m_name = p._modelName
                        config = room.member_configs.get(m_name, {})
                        members.append({
                            "name": m_name, 
                            "is_user": False,
                            "is_manager": config.get("is_manager", False),
                            "custom_prompt": config.get("custom_prompt", ""),
                            "avatar": config.get("avatar", "")
                        })
                    
                    await websocket.send_json({
                        "type": "members",
                        "members": members,
                        "group_name": room.group_name
                    })
                
                elif data["type"] == "get_history":
                    # 获取历史记录
                    await websocket.send_json({
                        "type": "history",
                        "messages": room.history
                    })
            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send_json({"type": "system", "content": f"处理请求时出错: {str(e)}"})
                
    except WebSocketDisconnect:
        room.disconnect(websocket)
    except Exception as e:
        print(f"WS Endpoint Error: {e}")
        room.disconnect(websocket)


@app.get("/")
async def root():
    return {"status": "ok", "message": "AI Group Chat WebSocket Server"}


@app.get("/rooms")
async def list_rooms():
    return {
        "rooms": [
            {
                "id": room_id,
                "clients": len(room.clients),
                "is_running": room.is_running,
                "message_count": len(room.history)
            }
            for room_id, room in rooms.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
