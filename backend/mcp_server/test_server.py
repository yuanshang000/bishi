"""
MCP Server 测试脚本

测试三个主要工具的功能
"""

import asyncio
import json
import sys
import io

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from server import fetch_learning_data, fetch_wrong_questions, fetch_weak_knowledge_points


async def test_fetch_learning_data():
    """测试获取学习数据"""
    print("\n" + "="*60)
    print("测试 1: fetch_learning_data")
    print("="*60)

    try:
        result = await fetch_learning_data({
            "student_id": 1,
            "limit": 10
        })

        data = json.loads(result[0].text)
        print(f"[成功] 成功获取 {data['total_records']} 条练习记录")
        if data['records']:
            print(f"\n最近一次练习：")
            record = data['records'][0]
            print(f"  - 章节: {record.get('chapter_title', 'N/A')}")
            print(f"  - 类型: {record['quiz_type']}")
            print(f"  - 分数: {record['score']}")
            print(f"  - 正确率: {record['accuracy']}%")
    except Exception as e:
        print(f"[失败] 测试失败: {e}")


async def test_fetch_wrong_questions():
    """测试获取错题记录"""
    print("\n" + "="*60)
    print("测试 2: fetch_wrong_questions")
    print("="*60)

    try:
        result = await fetch_wrong_questions({
            "student_id": 1,
            "is_mastered": False,
            "limit": 10
        })

        data = json.loads(result[0].text)
        print(f"[成功] 成功获取 {data['total_wrong_questions']} 道错题")
        if data['wrong_questions']:
            print(f"\n第一道错题：")
            question = data['wrong_questions'][0]
            print(f"  - 章节: {question.get('chapter_title', 'N/A')}")
            print(f"  - 类型: {question['question_type']}")
            print(f"  - 得分: {question['score']}")
            print(f"  - 重做次数: {question['retry_count']}")
            print(f"  - 已掌握: {'是' if question['is_mastered'] else '否'}")
    except Exception as e:
        print(f"[失败] 测试失败: {e}")


async def test_fetch_weak_knowledge_points():
    """测试获取薄弱知识点"""
    print("\n" + "="*60)
    print("测试 3: fetch_weak_knowledge_points")
    print("="*60)

    try:
        result = await fetch_weak_knowledge_points({
            "student_id": 1,
            "top_k": 5
        })

        data = json.loads(result[0].text)
        print(f"✅ 成功分析出 {data['total_weak_points']} 个薄弱知识点")

        if data['weak_knowledge_points']:
            print(f"\n薄弱知识点排行:")
            for i, kp in enumerate(data['weak_knowledge_points'], 1):
                print(f"  {i}. 知识点 {kp['knowledge_point_id']}")
                print(f"     错误次数: {kp['error_count']}")
                print(f"     相关章节: {kp['related_chapters']}")
                print(f"     题目类型: {kp['question_types']}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def main():
    """运行所有测试"""
    print("\n[启动] 开始测试 MCP Server 工具...")
    print("="*60)

    # 连接数据库
    from server import db
    try:
        db.connect()
        print("[成功] 数据库连接成功")
    except Exception as e:
        print(f"[失败] 数据库连接失败: {e}")
        return

    # 运行测试
    await test_fetch_learning_data()
    await test_fetch_wrong_questions()
    await test_fetch_weak_knowledge_points()

    # 关闭连接
    db.close()

    print("\n" + "="*60)
    print("[完成] 所有测试完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
