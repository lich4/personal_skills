import sqlite3
import json
import sys

def run_query(db_path, query, params=()):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sqlite_helper.py <db_path> <query> [param1 param2 ...]")
        sys.exit(1)
    db_path = sys.argv[1]
    query = sys.argv[2]
    params = sys.argv[3:]
    run_query(db_path, query, params)


