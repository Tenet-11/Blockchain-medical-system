from flask import Flask, request, jsonify, render_template
from blockchain import *
from blockchain_contract import (
    store_hash_on_chain,
    get_hash_from_chain,
    verify_hash_on_chain
)

app = Flask(__name__)

# =========================
# Step 7：Role-based Access Control
# =========================
ROLES = ["Doctor", "Patient", "Admin"]


def get_current_role():
    """從 request header 讀取目前使用者角色。"""
    return request.headers.get("X-Role", "Guest")


def get_current_patient_id():
    """Patient 角色用來判斷只能查看自己的病歷。"""
    return request.headers.get("X-Patient-Id", "").strip()


def forbidden(message="Permission denied"):
    return jsonify({
        "status": "FORBIDDEN",
        "error": message,
        "role": get_current_role()
    }), 403


def require_role(allowed_roles):
    """檢查目前角色是否有權限使用某個 API。"""
    role = get_current_role()

    if role not in allowed_roles:
        return forbidden(
            f"This action is only allowed for: {', '.join(allowed_roles)}"
        )

    return None


def can_patient_access_record(row):
    """
    row 格式：
    record_id, patient_id, doctor_name, diagnosis, prescription, timestamp, record_hash
    Patient 只能存取自己的 patient_id。
    Doctor / Admin 不受此限制。
    """
    role = get_current_role()

    if role in ["Doctor", "Admin"]:
        return True

    if role == "Patient":
        patient_id = get_current_patient_id()
        return patient_id != "" and row[1] == patient_id

    return False


def get_patient_history_from_blockchain(patient_id):
    """
    從目前記憶體中的 blockchain 查詢某位病患的所有歷史病歷。
    重點：不修改舊紀錄，而是依照區塊順序列出同一 patient_id 的所有 record。
    """
    history = []

    for block in blockchain.chain:
        if not isinstance(block.medical_record, MedicalRecord):
            continue

        record = block.medical_record
        if record.patient_id != patient_id:
            continue

        history.append({
            "block_index": block.index,
            "block_timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "block_hash": block.hash,
            "record_id": record.record_id,
            "patient_id": record.patient_id,
            "doctor_name": record.doctor_name,
            "diagnosis": record.diagnosis,
            "prescription": record.prescription,
            "record_timestamp": record.timestamp,
            "record_hash": record.calculate_hash()
        })

    return history


def store_record_hash_on_chain_safely(record):
    """
    將 MedicalRecord 的 hash 寫入 Solidity 合約。
    若鏈上已存在同一個 record_id，就不重複寫入，避免 Record already exists 錯誤。
    """
    record_hash = record.calculate_hash()

    try:
        chain_record = get_hash_from_chain(record.record_id)

        if chain_record["exists"]:
            return {
                "status": "ALREADY_EXISTS_ON_CHAIN",
                "record_id": record.record_id,
                "patient_id": chain_record["patient_id"],
                "on_chain_hash": chain_record["record_hash"],
                "message": "This record hash already exists on blockchain."
            }

        chain_result = store_hash_on_chain(
            record.record_id,
            record.patient_id,
            record_hash
        )

        return {
            "status": "STORED_ON_CHAIN",
            "record_id": record.record_id,
            "patient_id": record.patient_id,
            "record_hash": record_hash,
            "tx_hash": chain_result["tx_hash"],
            "block_number": chain_result["block_number"],
            "transaction_status": chain_result["status"]
        }

    except Exception as e:
        return {
            "status": "BLOCKCHAIN_ERROR",
            "record_id": record.record_id,
            "record_hash": record_hash,
            "error": str(e),
            "message": "SQLite operation may still succeed, but blockchain storage failed."
        }


def build_medical_record_from_db_row(row):
    """
    row 格式：
    record_id, patient_id, doctor_name, diagnosis, prescription, timestamp, record_hash
    """
    return MedicalRecord(
        record_id=row[0],
        patient_id=row[1],
        doctor_name=row[2],
        diagnosis=row[3],
        prescription=row[4],
        timestamp=row[5]
    )


# =========================
# 初始化 API 系統
# =========================
init_db()
blockchain = Blockchain()


def initialize_demo_data():
    """建立 demo 用的初始病歷資料。"""
    record1 = MedicalRecord("R001", "P001", "Dr. Wang", "Flu", "Medicine A")
    record2 = MedicalRecord("R002", "P002", "Dr. Lin", "Cold", "Medicine B")
    record3 = MedicalRecord("R003", "P003", "Dr. Chen", "Fever", "Medicine C")

    for record in [record1, record2, record3]:
        insert_record(record)
        blockchain.add_block(record)
        chain_result = store_record_hash_on_chain_safely(record)
        print(f"[CHAIN] Demo record {record.record_id}: {chain_result['status']}")


def load_blockchain_from_db():
    """
    從 SQLite 讀取目前已有的病歷資料，
    並重新建立記憶體中的 blockchain。
    """
    records = get_all_records()

    for r in records:
        record = MedicalRecord(
            record_id=r[0],
            patient_id=r[1],
            doctor_name=r[2],
            diagnosis=r[3],
            prescription=r[4],
            timestamp=r[5]
        )

        blockchain.add_block(record)


existing_records = get_all_records()

if len(existing_records) == 0:
    print("[INIT] Database is empty. Creating demo data...")
    initialize_demo_data()
else:
    print("[INIT] Existing records found. Loading blockchain from database...")
    load_blockchain_from_db()


# =========================
# 前端首頁 UI
# =========================
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# =========================
# API 1：查詢全部病歷
# Doctor / Admin 可以看全部
# Patient 只能看自己的 patient_id
# =========================
@app.route("/records", methods=["GET"])
def get_records():
    permission_error = require_role(["Doctor", "Patient", "Admin"])
    if permission_error:
        return permission_error

    records = get_all_records()

    result = []
    for r in records:
        if not can_patient_access_record(r):
            continue

        result.append({
            "record_id": r[0],
            "patient_id": r[1],
            "doctor_name": r[2],
            "diagnosis": r[3],
            "prescription": r[4],
            "timestamp": r[5],
            "hash": r[6]
        })

    return jsonify({
        "role": get_current_role(),
        "patient_id": get_current_patient_id() if get_current_role() == "Patient" else None,
        "records": result
    })


# =========================
# API 2：查詢單筆病歷
# Doctor / Admin 可以查任一筆
# Patient 只能查自己的病歷
# =========================
@app.route("/records/<record_id>", methods=["GET"])
def get_record(record_id):
    permission_error = require_role(["Doctor", "Patient", "Admin"])
    if permission_error:
        return permission_error

    r = get_record_by_id(record_id)

    if not r:
        return jsonify({"error": "Record not found"}), 404

    if not can_patient_access_record(r):
        return forbidden("Patients can only view their own medical records.")

    return jsonify({
        "record_id": r[0],
        "patient_id": r[1],
        "doctor_name": r[2],
        "diagnosis": r[3],
        "prescription": r[4],
        "timestamp": r[5],
        "hash": r[6]
    })


# =========================
# API 3：新增病歷
# Doctor / Admin 才能新增
# =========================
@app.route("/records", methods=["POST"])
def add_record():
    permission_error = require_role(["Doctor", "Admin"])
    if permission_error:
        return permission_error

    data = request.json

    required_fields = ["record_id", "patient_id", "doctor_name", "diagnosis", "prescription"]
    for field in required_fields:
        if field not in data or data[field] == "":
            return jsonify({"error": f"Missing field: {field}"}), 400

    if get_record_by_id(data["record_id"]):
        return jsonify({"error": "Record already exists"}), 409

    record = MedicalRecord(
        data["record_id"],
        data["patient_id"],
        data["doctor_name"],
        data["diagnosis"],
        data["prescription"]
    )

    insert_record(record)
    blockchain.add_block(record)
    chain_result = store_record_hash_on_chain_safely(record)

    return jsonify({
        "status": "SUCCESS",
        "message": "Record added successfully and hash was sent to blockchain.",
        "role": get_current_role(),
        "record_id": record.record_id,
        "patient_id": record.patient_id,
        "hash": record.calculate_hash(),
        "chain_result": chain_result
    })


# =========================
# API 4：驗證病歷完整性
# Doctor / Admin 可以驗證任一筆
# Patient 只能驗證自己的病歷
# =========================
@app.route("/verify/<record_id>", methods=["GET"])
def verify(record_id):
    permission_error = require_role(["Doctor", "Patient", "Admin"])
    if permission_error:
        return permission_error

    r = get_record_by_id(record_id)
    if not r:
        return jsonify({"error": "Record not found"}), 404

    if not can_patient_access_record(r):
        return forbidden("Patients can only verify their own medical records.")

    result = verify_record_from_db(record_id, blockchain)

    return jsonify({
        "record_id": record_id,
        "result": "VALID" if result else "INVALID"
    })


# =========================
# API 4-2：鏈上驗證病歷完整性
# 使用 Solidity 合約中保存的 on-chain hash 進行比對
# =========================
@app.route("/verify_on_chain/<record_id>", methods=["GET"])
def verify_on_chain(record_id):
    permission_error = require_role(["Doctor", "Patient", "Admin"])
    if permission_error:
        return permission_error

    r = get_record_by_id(record_id)
    if not r:
        return jsonify({"error": "Record not found in SQLite"}), 404

    if not can_patient_access_record(r):
        return forbidden("Patients can only verify their own medical records.")

    current_record = build_medical_record_from_db_row(r)
    current_hash = current_record.calculate_hash()

    try:
        chain_record = get_hash_from_chain(record_id)

        if not chain_record["exists"]:
            return jsonify({
                "status": "NOT_FOUND_ON_CHAIN",
                "result": "INVALID",
                "record_id": record_id,
                "current_hash": current_hash,
                "message": "This record hash was not found on blockchain."
            }), 404

        on_chain_hash = chain_record["record_hash"]
        is_valid = verify_hash_on_chain(record_id, current_hash)

        return jsonify({
            "status": "VALID" if is_valid else "INVALID",
            "result": "VALID" if is_valid else "INVALID",
            "record_id": record_id,
            "patient_id": r[1],
            "current_hash": current_hash,
            "on_chain_hash": on_chain_hash,
            "chain_timestamp": chain_record["timestamp"],
            "message": "Record matches blockchain hash."
                if is_valid else
                "Record has been tampered. Current hash does not match blockchain hash."
        })

    except Exception as e:
        return jsonify({
            "status": "BLOCKCHAIN_ERROR",
            "error": str(e),
            "record_id": record_id,
            "message": "Failed to verify record on blockchain."
        }), 500


# =========================
# API 5：查詢某位病患的完整歷史病歷
# Doctor / Admin 可以查任一病患
# Patient 只能查自己的歷史紀錄
# =========================
@app.route("/patients/<patient_id>/history", methods=["GET"])
def get_patient_history(patient_id):
    permission_error = require_role(["Doctor", "Patient", "Admin"])
    if permission_error:
        return permission_error

    if get_current_role() == "Patient" and get_current_patient_id() != patient_id:
        return forbidden("Patients can only view their own medical history.")

    history = get_patient_history_from_blockchain(patient_id)

    return jsonify({
        "patient_id": patient_id,
        "role": get_current_role(),
        "count": len(history),
        "history": history,
        "note": "History is read from blockchain blocks. Old records are preserved instead of being overwritten."
    })


# =========================
# API 6：更新病患病歷，也就是新增同一 patient_id 的新版本紀錄
# Doctor / Admin 才能新增歷史版本
# =========================
@app.route("/patients/<patient_id>/update", methods=["POST"])
def update_patient_record(patient_id):
    permission_error = require_role(["Doctor", "Admin"])
    if permission_error:
        return permission_error

    data = request.json or {}
    required_fields = ["record_id", "doctor_name", "diagnosis", "prescription"]

    for field in required_fields:
        if field not in data or data[field] == "":
            return jsonify({"error": f"Missing field: {field}"}), 400

    if get_record_by_id(data["record_id"]):
        return jsonify({"error": "Record already exists"}), 409

    record = MedicalRecord(
        data["record_id"],
        patient_id,
        data["doctor_name"],
        data["diagnosis"],
        data["prescription"]
    )

    insert_record(record)
    blockchain.add_block(record)
    chain_result = store_record_hash_on_chain_safely(record)

    return jsonify({
        "status": "SUCCESS",
        "message": "Patient medical history updated successfully and hash was sent to blockchain.",
        "explanation": "A new record was added for the same patient_id. The old record was not overwritten.",
        "role": get_current_role(),
        "record_id": record.record_id,
        "patient_id": record.patient_id,
        "hash": record.calculate_hash(),
        "chain_result": chain_result
    })


# =========================
# API 7：模擬竄改資料
# Demo 中設為 Admin 權限，避免一般使用者可竄改資料
# =========================
@app.route("/tamper/<record_id>", methods=["GET"])
def tamper(record_id):
    permission_error = require_role(["Admin"])
    if permission_error:
        return permission_error

    if not get_record_by_id(record_id):
        return jsonify({"error": "Record not found"}), 404

    tamper_database_record(record_id, "Cancer")

    return jsonify({
        "message": "Database record has been tampered",
        "role": get_current_role(),
        "record_id": record_id,
        "new_diagnosis": "Cancer"
    })


# =========================
# API 8：恢復被竄改的資料
# Admin 才能恢復資料
# =========================
@app.route("/restore/<record_id>", methods=["GET"])
def restore(record_id):
    permission_error = require_role(["Admin"])
    if permission_error:
        return permission_error

    if not get_record_by_id(record_id):
        return jsonify({
            "error": "Record not found in database",
            "record_id": record_id
        }), 404

    result = restore_record_from_blockchain(record_id, blockchain)

    if result:
        return jsonify({
            "message": "Record restored successfully",
            "role": get_current_role(),
            "record_id": record_id
        })
    else:
        return jsonify({
            "error": "Record could not be restored",
            "record_id": record_id
        }), 400


# =========================
# API 9：刪除指定病歷
# Admin 才能刪除資料
# =========================
@app.route("/records/<record_id>", methods=["DELETE"])
def delete_record(record_id):
    permission_error = require_role(["Admin"])
    if permission_error:
        return permission_error

    result = delete_record_from_db(record_id)

    if result:
        return jsonify({
            "message": "Record deleted successfully",
            "role": get_current_role(),
            "record_id": record_id
        })
    else:
        return jsonify({
            "error": "Record not found",
            "record_id": record_id
        }), 404


# =========================
# API 10：重置 demo 資料
# Admin 才能重置 demo
# =========================
@app.route("/reset", methods=["GET"])
def reset_demo():
    permission_error = require_role(["Admin"])
    if permission_error:
        return permission_error

    global blockchain

    reset_database()
    blockchain = Blockchain()
    initialize_demo_data()

    return jsonify({
        "message": "Demo data reset successfully",
        "role": get_current_role(),
        "records": ["R001", "R002", "R003"]
    })


if __name__ == "__main__":
    app.run(debug=True)
