"""
测试 MCP Server 是否能正常导入和初始化
"""
import sys
import os

# 切换到项目根目录
project_root = os.path.join(os.path.dirname(__file__), '..')
os.chdir(project_root)
sys.path.insert(0, project_root)

try:
    print("Testing MCP Server imports...")
    
    # 测试导入
    from app.core.database import SessionLocal
    print("OK: Database imported")
    
    from app.core.config import settings
    print(f"OK: Config imported: {settings.APP_NAME}")
    
    from app.models.wrong_question import WrongQuestion
    print("OK: Models imported")
    
    from app.services.rag_service import rag_service
    print("OK: RAG Service imported")
    
    from app.services.llm_service import llm_service
    print("OK: LLM Service imported")
    
    print("\nSUCCESS: All imports successful! MCP Server can start properly.")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
