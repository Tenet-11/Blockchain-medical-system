from datetime import datetime
import hashlib
import json
import sqlite3

DB_NAME = "medical_records.db"

def reset_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM medical_records")

    conn.commit()
    conn.close()

    print("[DB] Database reset.")


# 初始化資料庫
def init_db():
    # 連接資料庫（沒有就建立）
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 建立 medical_records 資料表
    # IF NOT EXISTS = 如果已存在就不會重建

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT NOT NULL UNIQUE,
        patient_id TEXT NOT NULL,
        doctor_name TEXT NOT NULL,
        diagnosis TEXT NOT NULL,
        prescription TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        record_hash TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


# 2️⃣ 插入資料
def insert_record(record):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO medical_records
        (record_id, patient_id, doctor_name, diagnosis, prescription, timestamp, record_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            record.record_id,
            record.patient_id,
            record.doctor_name,
            record.diagnosis,
            record.prescription,
            record.timestamp,
            record.calculate_hash()
        ))

        conn.commit()
        print(f"[DB] Record {record.record_id} inserted.")

    except sqlite3.IntegrityError:
        print(f"[DB] Record {record.record_id} already exists.")

    conn.close()


# 3️⃣ 查全部資料
def get_all_records():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT record_id, patient_id, doctor_name, diagnosis, prescription, timestamp, record_hash
    FROM medical_records
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# 4️⃣ 查單筆資料
def get_record_by_id(record_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT record_id, patient_id, doctor_name, diagnosis, prescription, timestamp, record_hash
    FROM medical_records
    WHERE record_id = ?
    """, (record_id,))

    row = cursor.fetchone()
    conn.close()

    return row


# 5️⃣ 顯示資料庫內容（方便你截圖）
def display_database():
    records = get_all_records()

    print("\n" + "=" * 80)
    print("           SQLite Medical Records (Off-chain Storage)")
    print("=" * 80)

    if not records:
        print("No records found.")
        return

    for r in records:
        print(f"Record ID      : {r[0]}")
        print(f"Patient ID     : {r[1]}")
        print(f"Doctor Name    : {r[2]}")
        print(f"Diagnosis      : {r[3]}")
        print(f"Prescription   : {r[4]}")
        print(f"Timestamp      : {r[5]}")
        print(f"Record Hash    : {r[6]}")
        print("-" * 80)

# =========================
# Medical Record Class
# =========================
class MedicalRecord:
    def __init__(self, record_id, patient_id, doctor_name, diagnosis, prescription, timestamp=None):
        self.record_id = record_id
        self.patient_id = patient_id
        self.doctor_name = doctor_name
        self.diagnosis = diagnosis
        self.prescription = prescription
        
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "patient_id": self.patient_id,
            "doctor_name": self.doctor_name,
            "diagnosis": self.diagnosis,
            "prescription": self.prescription,
            "timestamp": self.timestamp
        }

    # Record Hash：驗證單筆病歷資料完整性
    def calculate_hash(self):
        record_string = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(record_string.encode()).hexdigest()

    def __str__(self):
        return (
            f"Record ID      : {self.record_id}\n"
            f"Patient ID     : {self.patient_id}\n"
            f"Doctor Name    : {self.doctor_name}\n"
            f"Diagnosis      : {self.diagnosis}\n"
            f"Prescription   : {self.prescription}\n"
            f"Timestamp      : {self.timestamp}\n"
            f"Record Hash    : {self.calculate_hash()}"
        )


# =========================
# Block Class
# =========================
class Block:
    def __init__(self, index, medical_record, previous_hash):
        self.index = index
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.medical_record = medical_record
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "medical_record": self.medical_record.to_dict() if isinstance(self.medical_record, MedicalRecord) else self.medical_record,
            "previous_hash": self.previous_hash
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(block_string.encode()).hexdigest()


# =========================
# Blockchain Class
# =========================
class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        genesis_record = "Genesis Block"
        return Block(0, genesis_record, "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, medical_record):
        latest_block = self.get_latest_block()

        new_block = Block(
            index=len(self.chain),
            medical_record=medical_record,
            previous_hash=latest_block.hash
        )
        self.chain.append(new_block)
    

    def find_block_by_record_id(self, record_id):
        for block in self.chain:
            if isinstance(block.medical_record, MedicalRecord):
                if block.medical_record.record_id == record_id:
                    return block
        return None

    # 驗證整條鏈是否有效
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                print(f"Block {i} hash is invalid!")
                return False

            if current_block.previous_hash != previous_block.hash:
                print(f"Block {i} previous hash is invalid!")
                return False

        return True

    # 顯示整條鏈
    def display_chain(self):
        print("\n" + "=" * 90)
        print("        Blockchain Medical Record Integrity Verification System")
        print("=" * 90)

        for block in self.chain:
            print(f"\n[ Block {block.index} ]")
            print("-" * 90)
            print(f"Block Timestamp : {block.timestamp}")
            print(f"Previous Hash   : {block.previous_hash}")
            print(f"Current Hash    : {block.hash}")

            print("\nMedical Record Info:")
            if isinstance(block.medical_record, MedicalRecord):
                print(block.medical_record)
            else:
                print(block.medical_record)

            print("-" * 90)

        print("=" * 90)

    # 單筆資料驗證（驗證某個 block）
    def verify_block(self, block_index):
        if block_index <= 0 or block_index >= len(self.chain):
            print("\nInvalid block index!")
            return False

        block = self.chain[block_index]

        if not isinstance(block.medical_record, MedicalRecord):
            print("\nThis block does not contain a medical record.")
            return False

        stored_block_hash = block.hash
        recalculated_block_hash = block.calculate_hash()

        stored_record_hash = block.medical_record.calculate_hash()

        print("\n" + "=" * 90)
        print(f"                    Single Record Verification - Block {block_index}")
        print("=" * 90)
        print(f"Record ID              : {block.medical_record.record_id}")
        print(f"Patient ID             : {block.medical_record.patient_id}")
        print(f"Doctor Name            : {block.medical_record.doctor_name}")
        print(f"Diagnosis              : {block.medical_record.diagnosis}")
        print(f"Prescription           : {block.medical_record.prescription}")
        print(f"Timestamp              : {block.medical_record.timestamp}")
        print("-" * 90)
        print(f"Record Hash            : {stored_record_hash}")
        print(f"Stored Block Hash      : {stored_block_hash}")
        print(f"Recalculated Block Hash: {recalculated_block_hash}")

        if stored_block_hash == recalculated_block_hash:
            print("Verification Result    : VALID")
            print("=" * 90)
            return True
        else:
            print("Verification Result    : INVALID (Data Tampered)")
            print("=" * 90)
            return False


def verify_record_from_db(record_id, blockchain=None):
    row = get_record_by_id(record_id)

    if not row:
        print("Record not found in database.")
        return False

    # 從 SQLite 資料重建 MedicalRecord
    db_record = MedicalRecord(
        record_id=row[0],
        patient_id=row[1],
        doctor_name=row[2],
        diagnosis=row[3],
        prescription=row[4],
        timestamp=row[5]
    )

    # 重新計算目前資料的 hash
    recalculated_hash = db_record.calculate_hash()

    # SQLite 中原本儲存的 hash
    stored_hash = row[6]

    print("\n" + "=" * 90)
    print("                 Database Integrity Verification")
    print("=" * 90)
    print(f"Record ID          : {record_id}")
    print(f"Stored DB Hash     : {stored_hash}")
    print(f"Recalculated Hash  : {recalculated_hash}")

    if recalculated_hash == stored_hash:
        print("Result             : VALID")
        print("=" * 90)
        return True
    else:
        print("Result             : INVALID (Data Tampered)")
        print("=" * 90)
        return False
    

def tamper_database_record(record_id, new_diagnosis):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE medical_records
    SET diagnosis = ?
    WHERE record_id = ?
    """, (new_diagnosis, record_id))

    conn.commit()
    conn.close()

    print(f"[DB] Record {record_id} diagnosis changed to {new_diagnosis}.")


# =========================
# Main Program (Demo for Step 4)
# =========================

if __name__ == "__main__":
    init_db()

    record1 = MedicalRecord("R001", "P001", "Dr. Wang", "Flu", "Medicine A")
    record2 = MedicalRecord("R002", "P002", "Dr. Lin", "Cold", "Medicine B")
    record3 = MedicalRecord("R003", "P003", "Dr. Chen", "Fever", "Medicine C")

    blockchain = Blockchain()
    blockchain.add_block(record1)
    blockchain.add_block(record2)
    blockchain.add_block(record3)

    print("\n=== Inserting Records into SQLite ===")
    insert_record(record1)
    insert_record(record2)
    insert_record(record3)

    print("\n=== Display All Records (SQLite) ===")
    display_database()

    print("\n=== Verify Record R002 Before Tampering ===")
    verify_record_from_db("R002", blockchain)

    print("\n=== Tampering Database Record R002 ===")
    tamper_database_record("R002", "Cancer")

    print("\n=== Verify Record R002 After Tampering ===")
    verify_record_from_db("R002", blockchain)