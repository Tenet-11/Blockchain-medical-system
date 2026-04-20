from datetime import datetime
import hashlib
import json


# =========================
# Medical Record Class
# =========================
class MedicalRecord:
    def __init__(self, record_id, patient_id, doctor_name, diagnosis, prescription):
        self.record_id = record_id
        self.patient_id = patient_id
        self.doctor_name = doctor_name
        self.diagnosis = diagnosis
        self.prescription = prescription

        current_time = datetime.now()
        self.timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")

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


# =========================
# Main Program
# =========================
record1 = MedicalRecord("R001", "P001", "Dr. Wang", "Flu", "Medicine A")
record2 = MedicalRecord("R002", "P002", "Dr. Lin", "Cold", "Medicine B")
record3 = MedicalRecord("R003", "P003", "Dr. Chen", "Fever", "Medicine C")

blockchain = Blockchain()
blockchain.add_block(record1)
blockchain.add_block(record2)
blockchain.add_block(record3)

# 1. 顯示原始區塊鏈
print("\n=== Original Blockchain ===")
blockchain.display_chain()

# 2. 驗證整條鏈
print("\n=== Full Blockchain Validation ===")
print("Is blockchain valid?", blockchain.is_chain_valid())

# 3. 驗證單筆資料（Block 2）
print("\n=== Verify Single Record Before Tampering ===")
blockchain.verify_block(2)

# 4. 模擬竄改資料
print("\n=== Tampering with Block 2 ===")
blockchain.chain[2].medical_record.diagnosis = "Cancer"

# 5. 再次驗證單筆資料
print("\n=== Verify Single Record After Tampering ===")
blockchain.verify_block(2)

# 6. 再驗證整條鏈
print("\n=== Full Blockchain Validation After Tampering ===")
print("Is blockchain valid after tampering?", blockchain.is_chain_valid())