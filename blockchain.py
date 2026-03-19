from datetime import datetime
import hashlib   # Python用來做雜湊運算的模組
import json      # 把 dictionary 轉成穩定格式字串

# hash: 把一份資料丟進機器裡，吐出一串固定長度的亂碼

class MedicalRecord:
    def __init__(self,record_id,patient_id,doctor_name,diagnosis,prescription):
        self.record_id=record_id
        self.patient_id=patient_id
        self.doctor_name = doctor_name
        self.diagnosis = diagnosis
        self.prescription = prescription # 處方

        # 取得現在時間
        current_time=datetime.now()
        formatted_time=current_time.strftime("%Y-%m-%d %H:%M:%S")  # 把時間轉換成指定格式的字串
        self.timestamp=formatted_time

    def to_dict(self):

        # 回傳一個字典
        return{
            "record_id": self.record_id,
            "patient_id": self.patient_id,
            "doctor_name": self.doctor_name,
            "diagnosis": self.diagnosis,
            "prescription": self.prescription,
            "timestamp": self.timestamp
        }
    
    # MedicalRecord hash = 驗證資料完整性
    def calculate_hash(self):
        record_string=json.dumps(self.to_dict(),sort_keys=True)

        # encode是把字串轉位元資料，hexigest轉16進位
        return hashlib.sha256(record_string.encode()).hexdigest()


# Block就是區塊鏈裡的一格(一本病歷記錄冊的一頁)
class Block:
    def __init__(self,index,medical_record,previous_hash):
        self.index=index
        self.timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.medical_record=medical_record
        self.previous_hash=previous_hash
        self.hash=self.calculate_hash()
    
    def calculate_hash(self):
        block_string=json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "medical_record": self.medical_record.to_dict() if isinstance(self.medical_record, MedicalRecord) else self.medical_record,
            "previous_hash": self.previous_hash
        },sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain=[self.create_genesis_block()]

    def create_genesis_block(self):
        genesis_record="Genesis Block"
        return Block(0,genesis_record,"0")
    
    def get_latest_block(self):
        return self.chain[-1] # 取最後一個元素
    
    def add_block(self,medical_record):
        latest_block=self.get_latest_block()

        new_block=Block(
            index=len(self.chain),
            medical_record=medical_record,
            previous_hash=latest_block.hash
        )
        self.chain.append(new_block)
    
    def is_chain_valid(self):
        for i in range(1,len(self.chain)):
            current_block=self.chain[i]
            previous_block=self.chain[i-1]

            # 驗證目前區塊的hash是否正確
            if current_block.hash !=current_block.calculate_hash():
                print(f"Block {i} hash is invalid!")
                return False
        
            # 驗證previous_hash 是否正確連到前一個區塊
            if current_block.previous_hash!=previous_block.hash:
                print(f"Block {i} previous hash is invalid!")
                return False
        
        return True
    
    def display_chain(self):
        for block in self.chain:
            print("=" * 50)
            print(f"Block Index     : {block.index}")
            print(f"Timestamp       : {block.timestamp}")
            print(f"Previous Hash   : {block.previous_hash}")
            print(f"Current Hash    : {block.hash}")
            print(f"Medical Record  : {block.medical_record}")
        
        print("=" * 50)





 # ===== Main Program =====
record1 = MedicalRecord("R001", "P001", "Dr. Wang", "Flu", "Medicine A")
record2 = MedicalRecord("R002", "P002", "Dr. Lin", "Cold", "Medicine B")
record3 = MedicalRecord("R003", "P003", "Dr. Chen", "Fever", "Medicine C")

blockchain=Blockchain()
blockchain.add_block(record1)
blockchain.add_block(record2)
blockchain.add_block(record3)

print("=== Original Blockchain ===")
blockchain.display_chain()

print("Is blockchain valid?", blockchain.is_chain_valid())

# 模擬竄改
print("\n=== Tampering with Block 2 ===")
blockchain.chain[2].medical_record.diagnosis ="Cancer"

print("Is blockchain valid after tempering?",blockchain.is_chain_valid())

