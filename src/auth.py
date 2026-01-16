"""JWT认证工具模块
提供JWT token生成、验证、密码加密等功能
"""
import jwt
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from functools import wraps
from flask import request, jsonify, current_app


# ============================================================================
# 密码加密
# ============================================================================

def hash_password(password: str) -> str:
    """
    使用SHA256加密密码

    Args:
        password: 明文密码

    Returns:
        加密后的密码（十六进制字符串）
    """
    # 添加盐值（使用项目名称作为固定盐值）
    salt = "nuc_literature_analysis_system"
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码

    Args:
        password: 明文密码
        password_hash: 加密后的密码

    Returns:
        是否匹配
    """
    return hash_password(password) == password_hash


# ============================================================================
# JWT Token管理
# ============================================================================

SECRET_KEY = "nuc-literature-analysis-secret-key-2025"  # 生产环境应从环境变量读取
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # Token有效期：7天


def generate_token(user_id: int, username: str, email: str) -> str:
    """
    生成JWT token

    Args:
        user_id: 用户ID
        username: 用户名
        email: 邮箱

    Returns:
        JWT token字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
        'iat': datetime.now(timezone.utc),
        'type': 'access'
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str) -> Optional[Dict]:
    """
    解码JWT token

    Args:
        token: JWT token字符串

    Returns:
        解码后的payload，如果token无效则返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token已过期
        return None
    except jwt.InvalidTokenError:
        # Token无效
        return None


# ============================================================================
# 装饰器：保护路由
# ============================================================================

def auth_required(f):
    """
    路由保护装饰器：要求用户已登录
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'success': False,
                'error': '缺少认证token'
            }), 401

        # 提取Bearer token
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
        except IndexError:
            return jsonify({
                'success': False,
                'error': '认证token格式错误'
            }), 401

        # 验证token
        payload = decode_token(token)

        if not payload:
            return jsonify({
                'success': False,
                'error': 'Token无效或已过期'
            }), 401

        # 将用户信息添加到请求上下文
        request.current_user_id = payload.get('user_id')
        request.current_username = payload.get('username')
        request.current_email = payload.get('email')

        return f(*args, **kwargs)

    return decorated_function


def get_current_user_id() -> Optional[int]:
    """
    获取当前登录用户ID（从请求上下文中）

    Returns:
        用户ID，如果未登录则返回None
    """
    return getattr(request, 'current_user_id', None)


def get_current_user_info() -> Optional[Dict]:
    """
    获取当前登录用户信息（从请求上下文中）

    Returns:
        用户信息字典，如果未登录则返回None
    """
    if hasattr(request, 'current_user_id'):
        return {
            'user_id': request.current_user_id,
            'username': request.current_username,
            'email': request.current_email
        }
    return None
