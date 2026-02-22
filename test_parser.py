
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath("backend"))

from app.services.course_parser import CourseParserService
from app.core.database import SessionLocal
from app.models.chapter import Chapter
from app.models.subsection import SubSection

def test_parsing():
    db = SessionLocal()
    parser = CourseParserService(db)
    
    file_path = r"c:\Users\lala\Desktop\毕设\bishe\测试模板 - 副本.md"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    print("Parsing content...")
    try:
        # Parse into a new chapter or existing?
        # The parser creates a new chapter if not provided.
        # To avoid clutter, let's just see if it parses the min_questions correctly.
        # We can look at the code logic or run it.
        # Running it might create data in DB.
        # Let's check if we can dry run or just inspect the logic with a small snippet.
        
        # Extract a snippet that contains the min_questions
        snippet = """
[章节] Test Chapter
[节] Test Section
[小目标] Test Subsection
●目标描述：能够准确拼写并使用商务会面场景下的高频词汇。
●权重占比：20%
●合格分数：85分
●最少题数：15道
"""
        chapter = parser.parse_with_strict_rules(snippet)
        
        # Check the created subsection
        # Get the latest chapter
        if chapter:
            print(f"Chapter created: {chapter.title}")
            for section in chapter.sections:
                for sub in section.subsections:
                    print(f"Subsection: {sub.title}")
                    print(f"Min Questions: {sub.min_questions}")
                    if sub.min_questions == 15:
                        print("SUCCESS: Min questions parsed correctly.")
                    else:
                        print(f"FAILURE: Expected 15, got {sub.min_questions}")
                        
            # Cleanup (optional, but good for testing)
            # db.delete(chapter)
            # db.commit()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_parsing()
