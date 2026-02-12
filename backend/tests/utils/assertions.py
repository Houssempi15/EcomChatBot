"""
断言辅助函数
"""
from typing import Any, Dict, Optional
import httpx


def assert_success(
    response: httpx.Response,
    status_code: int = 200,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    断言API响应成功
    
    Args:
        response: HTTP响应对象
        status_code: 期望的状态码
        message: 自定义错误消息
        
    Returns:
        响应数据字典
    """
    # 检查状态码
    if response.status_code != status_code:
        error_msg = message or f"状态码错误: 期望 {status_code}, 实际 {response.status_code}"
        try:
            error_detail = response.json()
            error_msg += f"\n响应内容: {error_detail}"
        except Exception:
            error_msg += f"\n响应内容: {response.text}"
        raise AssertionError(error_msg)
    
    # 解析JSON
    try:
        data = response.json()
    except Exception as e:
        raise AssertionError(f"响应不是有效的JSON: {str(e)}\n响应内容: {response.text}")
    
    # 检查success字段
    if "success" in data and not data.get("success"):
        error_msg = message or "API返回失败"
        if "error" in data:
            error_msg += f"\n错误信息: {data['error']}"
        raise AssertionError(error_msg)
    
    # 返回data字段
    if "data" in data:
        return data["data"]
    
    return data


def assert_error(
    response: httpx.Response,
    expected_status: int = 400,
    expected_code: Optional[str] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    断言API返回错误
    
    Args:
        response: HTTP响应对象
        expected_status: 期望的错误状态码
        expected_code: 期望的错误代码
        message: 自定义错误消息
        
    Returns:
        错误信息字典
    """
    # 检查状态码
    if response.status_code != expected_status:
        error_msg = message or f"状态码错误: 期望 {expected_status}, 实际 {response.status_code}"
        raise AssertionError(error_msg)
    
    # 解析JSON
    try:
        data = response.json()
    except Exception as e:
        raise AssertionError(f"响应不是有效的JSON: {str(e)}")
    
    # 检查success字段应为False
    if data.get("success") is not False:
        raise AssertionError("错误响应中success字段应为False")
    
    # 检查error字段
    if "error" not in data:
        raise AssertionError("错误响应中应包含error字段")
    
    # 检查错误代码
    if expected_code:
        error = data["error"]
        if isinstance(error, dict):
            actual_code = error.get("code")
        else:
            actual_code = None
        
        if actual_code != expected_code:
            raise AssertionError(
                f"错误代码不匹配: 期望 {expected_code}, 实际 {actual_code}"
            )
    
    return data["error"]


def assert_paginated(
    data: Dict[str, Any],
    min_total: int = 0,
    check_items: bool = True
) -> Dict[str, Any]:
    """
    断言分页响应格式
    
    Args:
        data: 响应数据
        min_total: 最小总数
        check_items: 是否检查items字段
        
    Returns:
        响应数据
    """
    # 检查分页字段
    required_fields = ["items", "total", "page", "size", "pages"]
    for field in required_fields:
        if field not in data:
            raise AssertionError(f"分页响应缺少必需字段: {field}")
    
    # 检查总数
    if data["total"] < min_total:
        raise AssertionError(
            f"总数不足: 期望至少 {min_total}, 实际 {data['total']}"
        )
    
    # 检查items是否为列表
    if check_items and not isinstance(data["items"], list):
        raise AssertionError("items字段应为列表类型")
    
    # 检查分页计算是否正确
    expected_pages = (data["total"] + data["size"] - 1) // data["size"]
    if data["pages"] != expected_pages:
        raise AssertionError(
            f"分页计算错误: 期望 {expected_pages} 页, 实际 {data['pages']} 页"
        )
    
    return data


def assert_field_exists(data: Dict[str, Any], field: str, message: Optional[str] = None):
    """断言字段存在"""
    if field not in data:
        error_msg = message or f"缺少必需字段: {field}"
        raise AssertionError(error_msg)


def assert_field_type(
    data: Dict[str, Any],
    field: str,
    expected_type: type,
    message: Optional[str] = None
):
    """断言字段类型"""
    assert_field_exists(data, field)
    
    if not isinstance(data[field], expected_type):
        error_msg = message or (
            f"字段 {field} 类型错误: "
            f"期望 {expected_type.__name__}, "
            f"实际 {type(data[field]).__name__}"
        )
        raise AssertionError(error_msg)


def assert_response_time(response: httpx.Response, max_time: float = 1.0):
    """断言响应时间"""
    elapsed = response.elapsed.total_seconds()
    if elapsed > max_time:
        raise AssertionError(
            f"响应时间过长: {elapsed:.2f}s > {max_time}s"
        )
