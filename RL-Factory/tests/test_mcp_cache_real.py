#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP工具缓存功能真实测试脚本
直接使用工具管理器测试web_search工具的缓存功能
"""
import os
import sys
import time
import json
import subprocess
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from omegaconf import OmegaConf

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from envs.tool_manager.qwen3_manager import QwenManager
from redis_server.client import RedisClient


class RealMCPCacheTester:
    """真实MCP缓存功能测试器"""
    
    def __init__(self):
        self.redis_client = None
        self.tool_manager = None
        self.test_queries = [
            "Python编程教程",
            "机器学习算法", 
            "深度学习框架",
            "人工智能发展历史",
            "自然语言处理技术"
        ]
        self.duplicate_queries = [
            "Python编程教程",  # 重复查询
            "机器学习算法",    # 重复查询
            "人工智能发展历史",      # 新查询
            "自然语言处理技术"       # 新查询
        ]
        self.redis_stats_before = {}
        self.redis_stats_after = {}
        
    def start_redis_service(self) -> bool:
        """启动Redis服务"""
        print("🚀 启动Redis服务...")
        try:
            redis_script = project_root / "redis_server" / "start_redis.sh"
            result = subprocess.run(
                [str(redis_script), "start"], 
                capture_output=True, 
                text=True, 
                cwd=project_root / "redis_server"
            )
            
            if result.returncode == 0:
                print("✅ Redis服务启动成功")
                time.sleep(3)  # 等待服务完全启动
                return True
            else:
                print(f"❌ Redis服务启动失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 启动Redis服务时出错: {e}")
            return False
    
    def stop_redis_service(self) -> bool:
        """停止Redis服务"""
        print("🛑 停止Redis服务...")
        try:
            redis_script = project_root / "redis_server" / "start_redis.sh"
            result = subprocess.run(
                [str(redis_script), "stop"], 
                capture_output=True, 
                text=True, 
                cwd=project_root / "redis_server"
            )
            
            if result.returncode == 0:
                print("✅ Redis服务停止成功")
                return True
            else:
                print(f"⚠️ Redis服务停止时出现警告: {result.stderr}")
                return True  # 即使有警告也认为成功
        except Exception as e:
            print(f"❌ 停止Redis服务时出错: {e}")
            return False
    
    def check_redis_status(self) -> bool:
        """检查Redis服务状态"""
        try:
            redis_script = project_root / "redis_server" / "start_redis.sh"
            result = subprocess.run(
                [str(redis_script), "status"], 
                capture_output=True, 
                text=True, 
                cwd=project_root / "redis_server"
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 检查Redis状态时出错: {e}")
            return False
    
    def init_redis_connection(self) -> bool:
        """初始化Redis连接"""
        try:
            self.redis_client = RedisClient(host='localhost', port=6379)
            print("✅ Redis连接初始化成功")
            return True
        except Exception as e:
            print(f"❌ Redis连接初始化失败: {e}")
            return False
    
    def init_tool_manager(self) -> bool:
        """初始化工具管理器"""
        try:
            # 创建配置
            config = {
                'mcp_mode': 'sse',
                'config_path': 'envs/configs/sse_mcp_tools.pydata',
                'tool_name_selected': [],  # 使用所有可用工具
                'enable_redis_cache': True,
                'redis_host': 'localhost',
                'redis_port': 6379,
                'cache_ttl': 0,  # 永不过期
                'cache_prefix': 'mcp_tool',
                'cache_logging': True,
                'enable_limiter': False,
                'max_concurrency': 100,
                'parallel_sse_tool_call': {
                    'is_enabled': False,
                    'num_instances': 1
                }
            }
            
            self.tool_manager = QwenManager(config)
            print("✅ 工具管理器初始化成功")
            print(f"📋 可用工具: {list(self.tool_manager.tool_map.keys())}")
            return True
        except Exception as e:
            print(f"❌ 工具管理器初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_redis_stats(self) -> Dict[str, Any]:
        """获取Redis统计信息"""
        try:
            if self.redis_client:
                stats = self.redis_client.get_stats()
                return stats
            return {}
        except Exception as e:
            print(f"❌ 获取Redis统计信息失败: {e}")
            return {}
    
    def clear_test_cache_data(self) -> bool:
        """清除测试相关的缓存数据"""
        try:
            if not self.redis_client:
                print("❌ Redis客户端未初始化")
                return False
            
            print("🧹 清除测试相关的缓存数据...")
            
            # 获取所有测试查询的缓存键
            test_queries = self.test_queries + self.duplicate_queries
            cleared_count = 0
            
            for query in test_queries:
                # 构造工具调用参数（与工具管理器中的逻辑一致）
                tool_args = {"query": query}
                
                # 生成缓存键（使用工具管理器的缓存管理器）
                cache_key = self.tool_manager.cache_manager.get_cache_key(
                    "mcp_tool", 
                    f"meituan_search-web_search:{tool_args}"
                )
                
                # 删除缓存
                if self.redis_client.delete_cache(cache_key):
                    cleared_count += 1
            
            print(f"✅ 已清除 {cleared_count} 个测试缓存项")
            return True
            
        except Exception as e:
            print(f"❌ 清除测试缓存数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def call_web_search_tool(self, query: str) -> Dict[str, Any]:
        """调用web_search工具
        
        MCP架构说明：
        - meituan_search: MCP服务器名称
        - web_search: MCP服务器提供的工具名称
        - 完整工具名称: meituan_search-web_search
        """
        try:
            # 构造工具调用参数（需要是JSON字符串格式）
            tool_args = json.dumps({"query": query})
            
            # 调用MCP工具：meituan_search服务器上的web_search工具
            mcp_server = "meituan_search"
            tool_name = "web_search"
            full_tool_name = f"{mcp_server}-{tool_name}"
            
            print(f"🔧 调用MCP工具: {full_tool_name} (服务器: {mcp_server}, 工具: {tool_name})")
            result = self.tool_manager._call_tool(full_tool_name, tool_args)
            
            return {
                "query": query,
                "mcp_server": mcp_server,
                "tool_name": tool_name,
                "full_tool_name": full_tool_name,
                "result": result,
                "success": True,
                "timestamp": time.time()
            }
        except Exception as e:
            print(f"❌ MCP工具调用失败: {e}")
            return {
                "query": query,
                "mcp_server": "meituan_search",
                "tool_name": "web_search",
                "full_tool_name": "meituan_search-web_search",
                "result": str(e),
                "success": False,
                "timestamp": time.time()
            }
    
    def run_cache_tests(self) -> Dict[str, Any]:
        """运行缓存测试"""
        print("\n" + "="*60)
        print("🧪 开始MCP缓存功能真实测试")
        print("="*60)
        
        test_results = {
            "initial_queries": [],
            "duplicate_queries": [],
            "cache_hit_rate": 0.0,
            "redis_stats_before": self.redis_stats_before,
            "redis_stats_after": self.redis_stats_after,
            "total_queries": 0,
            "successful_queries": 0
        }
        
        # 测试1: 首次查询（应该不命中缓存）
        print("\n📝 测试1: 首次查询（应该不命中缓存）")
        print("-" * 40)
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n查询 {i}: {query}")
            result = self.call_web_search_tool(query)
            test_results["initial_queries"].append(result)
            test_results["total_queries"] += 1
            
            if result["success"]:
                test_results["successful_queries"] += 1
                print("✅ 查询成功")
                print(f"📄 查询结果: {result['result'][:200]}..." if len(str(result['result'])) > 200 else f"📄 查询结果: {result['result']}")
            else:
                print("❌ 查询失败")
        
        # 测试2: 重复查询（应该命中缓存）
        print("\n📝 测试2: 重复查询（应该命中缓存）")
        print("-" * 40)
        
        cache_hits = 0
        total_duplicate_queries = len(self.duplicate_queries)
        
        for i, query in enumerate(self.duplicate_queries, 1):
            print(f"\n重复查询 {i}: {query}")
            result = self.call_web_search_tool(query)
            test_results["duplicate_queries"].append(result)
            test_results["total_queries"] += 1
            
            if result["success"]:
                test_results["successful_queries"] += 1
                print("✅ 查询成功")
                print(f"📄 查询结果: {result['result'][:200]}..." if len(str(result['result'])) > 200 else f"📄 查询结果: {result['result']}")
                # 注意：这里我们无法直接判断是否命中缓存，因为工具管理器内部处理
                # 但我们可以通过Redis统计信息来间接判断
            else:
                print("❌ 查询失败")
        
        # 获取测试后的Redis统计信息
        self.redis_stats_after = self.get_redis_stats()
        
        # 更新test_results中的redis_stats_after
        test_results["redis_stats_after"] = self.redis_stats_after
        
        # 计算缓存命中率（基于Redis统计信息）
        stats_before = test_results["redis_stats_before"]
        stats_after = test_results["redis_stats_after"]
        
        total_hits = stats_after.get('keyspace_hits', 0) - stats_before.get('keyspace_hits', 0)
        total_misses = stats_after.get('keyspace_misses', 0) - stats_before.get('keyspace_misses', 0)
        
        if total_hits + total_misses > 0:
            test_results["cache_hit_rate"] = total_hits / (total_hits + total_misses)
        else:
            test_results["cache_hit_rate"] = 0.0
        
        return test_results
    
    def analyze_results(self, test_results: Dict[str, Any]) -> None:
        """分析测试结果"""
        print("\n" + "="*60)
        print("📊 测试结果分析")
        print("="*60)
        
        # 基本统计
        total_queries = test_results["total_queries"]
        successful_queries = test_results["successful_queries"]
        success_rate = successful_queries / total_queries if total_queries > 0 else 0
        
        print(f"\n📈 查询统计:")
        print(f"  总查询数: {total_queries}")
        print(f"  成功查询数: {successful_queries}")
        print(f"  成功率: {success_rate:.2%}")
        
        # 缓存命中率分析
        cache_hit_rate = test_results["cache_hit_rate"]
        print(f"\n🎯 缓存命中率: {cache_hit_rate:.2%}")
        
        if cache_hit_rate >= 0.3:  # 至少30%的查询应该命中缓存
            print("✅ 缓存功能工作正常")
        else:
            print("⚠️ 缓存功能可能存在问题或需要更多重复查询")
        
        # Redis内存使用分析
        stats_before = test_results["redis_stats_before"]
        stats_after = test_results["redis_stats_after"]
        
        print(f"\n💾 Redis内存使用情况:")
        print(f"  测试前: {stats_before.get('used_memory_human', 'N/A')}")
        print(f"  测试后: {stats_after.get('used_memory_human', 'N/A')}")
        
        # 命令处理统计
        print(f"\n📈 Redis命令处理统计:")
        print(f"  总命令数: {stats_after.get('total_commands_processed', 0)}")
        print(f"  缓存命中: {stats_after.get('keyspace_hits', 0)}")
        print(f"  缓存未命中: {stats_after.get('keyspace_misses', 0)}")
        
        # 详细查询结果
        print(f"\n📋 详细查询结果:")
        print(f"  首次查询数量: {len(test_results['initial_queries'])}")
        print(f"  重复查询数量: {len(test_results['duplicate_queries'])}")
        
        # 显示成功的查询
        successful_initial = [r for r in test_results['initial_queries'] if r['success']]
        successful_duplicate = [r for r in test_results['duplicate_queries'] if r['success']]
        
        print(f"\n✅ 成功的查询:")
        print(f"  首次查询成功: {len(successful_initial)}")
        print(f"  重复查询成功: {len(successful_duplicate)}")
        
        # 显示MCP架构信息
        if successful_initial:
            first_result = successful_initial[0]
            print(f"\n🏗️ MCP架构信息:")
            print(f"  MCP服务器: {first_result.get('mcp_server', 'N/A')}")
            print(f"  工具名称: {first_result.get('tool_name', 'N/A')}")
            print(f"  完整工具名称: {first_result.get('full_tool_name', 'N/A')}")
        
        # 显示失败的查询
        failed_queries = [r for r in test_results['initial_queries'] + test_results['duplicate_queries'] if not r['success']]
        if failed_queries:
            print(f"\n❌ 失败的查询:")
            for result in failed_queries:
                print(f"  - {result['query']}: {result['result']}")
    
    def run_full_test(self) -> bool:
        """运行完整测试流程"""
        print("🚀 开始MCP缓存功能完整真实测试")
        print("="*60)
        
        try:
            # 1. 启动Redis服务
            if not self.start_redis_service():
                print("❌ 无法启动Redis服务，测试终止")
                return False
            
            # 2. 检查Redis状态
            if not self.check_redis_status():
                print("❌ Redis服务未正常运行，测试终止")
                return False
            
            # 3. 初始化Redis连接
            if not self.init_redis_connection():
                print("❌ 无法连接到Redis，测试终止")
                return False
            
            # 4. 初始化工具管理器
            if not self.init_tool_manager():
                print("❌ 无法初始化工具管理器，测试终止")
                return False
            
            # 5. 清除测试相关的缓存数据
            if not self.clear_test_cache_data():
                print("⚠️ 清除测试缓存数据失败，继续测试")
            
            # 6. 获取测试前的Redis统计信息
            self.redis_stats_before = self.get_redis_stats()
            print(f"\n📊 测试前Redis状态: {self.redis_stats_before}")
            
            # 7. 运行缓存测试
            test_results = self.run_cache_tests()
            
            # 8. 分析结果
            self.analyze_results(test_results)
            
            print("\n✅ 测试完成!")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # 9. 清理：停止Redis服务
            self.stop_redis_service()


def main():
    """主函数"""
    print("🧪 MCP工具缓存功能真实测试脚本")
    print("="*60)
    
    tester = RealMCPCacheTester()
    success = tester.run_full_test()
    
    if success:
        print("\n🎉 所有测试完成!")
        sys.exit(0)
    else:
        print("\n💥 测试失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
