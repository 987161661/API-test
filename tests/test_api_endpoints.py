import sys
import os
import pytest
from fastapi.testclient import TestClient

# 将项目根目录添加到 python path 以便导入 chat_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_server import app

client = TestClient(app)

def test_set_group_name_success():
    """
    测试用例：设置群名称 - 正常情况
    
    测试场景：
        向存在的房间发送合法的群名称更新请求。
    预期结果：
        1. 接口返回状态码 200。
        2. 返回的 JSON 中 status 为 'success'。
        3. 返回的 group_name 与请求中的一致。
    """
    room_id = "consciousness_lab"
    payload = {
        "group_name": "相亲相爱一家人"
    }
    
    response = client.post(f"/control/{room_id}/group_name", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["group_name"] == "相亲相爱一家人"

def test_set_group_name_empty():
    """
    测试用例：设置群名称 - 边界情况（空名称）
    
    测试场景：
        发送空的 group_name。
    预期结果：
        接口应该处理这种情况，根据当前逻辑，如果 group_name 为空字符串或 None，
        可能不会更新或者置空。
        (根据 chat_server.py 代码: if request.group_name: room.update_group_name...)
        如果不传 group_name，则不会更新。
    """
    room_id = "consciousness_lab"
    # 先设置一个初始名
    client.post(f"/control/{room_id}/group_name", json={"group_name": "InitialName"})
    
    # 发送空名
    payload = {
        "group_name": ""
    }
    response = client.post(f"/control/{room_id}/group_name", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    # 根据逻辑，如果不满足 if request.group_name，则不更新，返回当前 group_name
    assert data["group_name"] == "InitialName"

def test_set_group_name_long_string():
    """
    测试用例：设置群名称 - 边界情况（超长名称）
    
    测试场景：
        发送一个超过一般长度限制的群名称。
    预期结果：
        虽然前端有限制，但后端目前没有显式限制长度。
        测试确认后端能接收并存储长字符串。
    """
    room_id = "consciousness_lab"
    long_name = "这是一段非常非常长的群名称用于测试系统的边界处理能力" * 2
    payload = {
        "group_name": long_name
    }
    
    response = client.post(f"/control/{room_id}/group_name", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["group_name"] == long_name

def test_set_group_name_special_chars():
    """
    测试用例：设置群名称 - 异常/特殊字符情况
    
    测试场景：
        发送包含特殊字符、表情符号的群名称。
    预期结果：
        后端应能正确处理并存储 Unicode 字符。
    """
    room_id = "consciousness_lab"
    special_name = "测试群组🚀✨@#¥%……&*"
    payload = {
        "group_name": special_name
    }
    
    response = client.post(f"/control/{room_id}/group_name", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["group_name"] == special_name
