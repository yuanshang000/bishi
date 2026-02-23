import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.document import CourseDocument
from app.models.subsection import SubSection
from app.services.rag_service import rag_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_vectors():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Clear ChromaDB
        print("Clearing ChromaDB...")
        try:
            count = rag_service.clear_all_vectors()
            print(f"Cleared {count} vectors from ChromaDB.")
        except Exception as e:
            print(f"Error clearing ChromaDB: {e}")

        # 2. Reset is_vectorized flag in database
        print("Resetting is_vectorized flags in database...")
        # Use execute with text() for update
        stmt = text("UPDATE course_documents SET is_vectorized = 0, vector_count = 0, chroma_ids = NULL")
        result = db.execute(stmt)
        db.commit()
        print(f"Reset flags for documents.")

        # 3. Fetch all documents and re-vectorize
        print("Re-vectorizing documents...")
        docs = db.query(CourseDocument).filter(CourseDocument.content.isnot(None)).all()
        print(f"Found {len(docs)} documents to vectorize.")

        success_count = 0
        for i, doc in enumerate(docs):
            print(f"Processing document {i+1}/{len(docs)}: {doc.title} (ID: {doc.id})...")
            try:
                # We need to use vectorize_document method
                # Note: vectorize_document commits to DB, so we should be careful with session
                if rag_service.vectorize_document(db, doc.id):
                    success_count += 1
                    print(f"  Successfully vectorized document {doc.id}")
                else:
                    print(f"  Failed to vectorize document {doc.id}")
            except Exception as e:
                print(f"  Error processing document {doc.id}: {e}")

        print(f"Finished vectorizing documents. Success: {success_count}/{len(docs)}.")

        # 4. Vectorize all SubSections
        print("Vectorizing SubSections...")
        subsections = db.query(SubSection).filter(SubSection.content.isnot(None)).all()
        print(f"Found {len(subsections)} subsections to vectorize.")

        sub_success_count = 0
        for i, sub in enumerate(subsections):
            print(f"Processing subsection {i+1}/{len(subsections)}: {sub.title} (ID: {sub.id})...")
            try:
                if rag_service.vectorize_subsection(db, sub.id):
                    sub_success_count += 1
                    print(f"  Successfully vectorized subsection {sub.id}")
                else:
                    print(f"  Failed to vectorize subsection {sub.id}")
            except Exception as e:
                print(f"  Error processing subsection {sub.id}: {e}")
        
        print(f"Finished vectorizing subsections. Success: {sub_success_count}/{len(subsections)}.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_vectors()
