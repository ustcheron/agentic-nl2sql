#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis客户端使用示例
演示如何连接和使用Redis缓存服务
"""
import redis
import json
import hashlib
from typing import Any, Optional

class RedisClient:
    """Redis客户端封装类"""
    
    def __init__(self, host='localhost', port=6379, db=0, password=None, default_permanent=False):
        """
        初始化Redis客户端
        """
        try:
            self.client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                password=password,
                decode_responses=True
            )
            # 测试连接
            self.client.ping()
            self.default_permanent = default_permanent
            print(f"✅ Redis连接成功: {host}:{port}")
            if default_permanent:
                print("🔒 默认永久缓存模式已启用")
        except redis.ConnectionError as e:
            print(f"❌ Redis连接失败: {e}")
            raise
    
    def set_cache(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        设置缓存
        """
        try:
            # 将值序列化为JSON
            json_value = json.dumps(value, ensure_ascii=False)
            
            # 确定TTL策略
            if ttl is None:
                # 使用默认策略
                if self.default_permanent:
                    ttl = 0  # 永久缓存
                else:
                    ttl = 2592000  # 30天
            
            if ttl == 0:
                # 永不过期
                result = self.client.set(key, json_value)
                print(f"📝 永久缓存设置: {key} -> {len(json_value)} bytes")
            else:
                # 有过期时间
                result = self.client.setex(key, ttl, json_value)
                print(f"📝 缓存设置: {key} -> {len(json_value)} bytes (TTL: {ttl}s)")
            
            return result
        except Exception as e:
            print(f"❌ 缓存设置失败: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        获取缓存
        """
        try:
            json_value = self.client.get(key)
            if json_value:
                value = json.loads(json_value)
                print(f"📖 缓存命中: {key}")
                return value
            else:
                print(f"🔍 缓存未命中: {key}")
                return None
        except Exception as e:
            print(f"❌ 缓存获取失败: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """
        删除缓存
        """
        try:
            result = self.client.delete(key)
            print(f"🗑️ 缓存删除: {key}")
            return bool(result)
        except Exception as e:
            print(f"❌ 缓存删除失败: {e}")
            return False
    
    def generate_key(self, query: str, prefix: str = "search") -> str:
        """
        生成缓存键
        """
        # 使用MD5哈希确保键的唯一性
        hash_value = hashlib.md5(query.encode('utf-8')).hexdigest()
        return f"{prefix}:{hash_value}"
    
    def get_stats(self) -> dict:
        """
        获取Redis统计信息
        """
        try:
            info = self.client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def set_permanent_cache(self, key: str, value: Any) -> bool:
        """
        设置永久缓存（永不过期）
        """
        return self.set_cache(key, value, ttl=0)
    
    def set_temporary_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        设置临时缓存（指定过期时间）
        """
        return self.set_cache(key, value, ttl=ttl)


def demo_usage():
    """演示Redis客户端的使用方法"""
    print("🚀 Redis客户端使用演示")
    print("=" * 50)
    
    # 初始化客户端
    try:
        redis_client = RedisClient()
    except Exception as e:
        print(f"初始化失败: {e}")
        return
    
    # 演示缓存操作
    print("\n📝 演示缓存操作:")
    
    # 1. 设置缓存
    test_data = {
        "query": "Python Redis教程",
        "results": [
            {"title": "Redis官方文档", "url": "https://redis.io/docs"},
            {"title": "Python Redis库", "url": "https://pypi.org/project/redis"}
        ],
        "timestamp": "2025-09-08T12:00:00Z"
    }
    
    key = redis_client.generate_key("Python Redis教程")
    
    # 演示不同缓存策略
    print("设置30天过期缓存...")
    redis_client.set_cache(key, test_data)  # 使用默认策略（30天）
    
    # 演示永久缓存
    permanent_key = redis_client.generate_key("永久缓存测试")
    print("设置永久缓存...")
    redis_client.set_permanent_cache(permanent_key, test_data)
    
    # 演示临时缓存
    temp_key = redis_client.generate_key("临时缓存测试")
    print("设置5分钟临时缓存...")
    redis_client.set_temporary_cache(temp_key, test_data, ttl=300)
    
    # 2. 获取缓存
    cached_data = redis_client.get_cache(key)
    if cached_data:
        print(f"获取到的数据: {cached_data['query']}")
    
    # 3. 再次获取（应该命中缓存）
    cached_data2 = redis_client.get_cache(key)
    
    # 4. 删除缓存
    redis_client.delete_cache(key)
    
    # 5. 获取统计信息
    print("\n📊 Redis统计信息:")
    stats = redis_client.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 演示完成!")


if __name__ == "__main__":
    # demo test
    demo_usage()
