#!/usr/bin/env python3
"""
API测试脚本 - 验证所有后端API是否正常工作
运行此脚本前，请确保后端服务已启动（python app.py）
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:5001"

def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def test_api(name: str, method: str, endpoint: str, data: Dict = None) -> bool:
    """测试单个API端点"""
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"测试: {name}")
        print(f"  URL: {method} {url}")

        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            print(f"  ❌ 不支持的HTTP方法: {method}")
            return False

        print(f"  状态码: {response.status_code}")

        if response.status_code < 400:
            try:
                result = response.json()
                if result.get('success'):
                    print(f"  ✅ 成功: {result.get('message', 'OK')}")
                    return True
                else:
                    print(f"  ❌ 业务错误: {result.get('error', '未知错误')}")
                    return False
            except json.JSONDecodeError:
                print(f"  ✅ 响应不是JSON格式")
                return True
        else:
            print(f"  ❌ HTTP错误: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  错误详情: {error_data}")
            except:
                print(f"  错误内容: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  ❌ 连接失败：后端服务未启动")
        return False
    except requests.exceptions.Timeout:
        print(f"  ❌ 请求超时")
        return False
    except Exception as e:
        print(f"  ❌ 异常: {str(e)}")
        return False

def main():
    """运行所有测试"""
    print("\n🔍 科研文献摘要提取系统 - API测试")
    print(f"测试服务器: {BASE_URL}")
    print(f"测试时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # 1. 基础接口
    print_section("1. 基础接口测试")
    results.append(("健康检查", test_api("健康检查", "GET", "/api/health")))
    results.append(("系统配置", test_api("系统配置", "GET", "/api/config")))

    # 2. 论文管理
    print_section("2. 论文管理接口")
    results.append(("论文列表", test_api("论文列表", "GET", "/api/papers")))

    # 3. 统计接口
    print_section("3. 统计信息接口")
    results.append(("统计信息", test_api("统计信息", "GET", "/api/statistics")))

    # 4. 研究空白接口
    print_section("4. 研究空白接口")
    results.append(("高优先级研究空白", test_api("高优先级研究空白", "GET", "/api/gaps/priority?limit=5")))

    # 5. 知识图谱接口
    print_section("5. 知识图谱接口")
    results.append(("知识图谱", test_api("知识图谱", "GET", "/api/knowledge-graph")))

    # 汇总结果
    print_section("测试结果汇总")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！后端API工作正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查后端服务。")
        return 1

if __name__ == "__main__":
    exit(main())
