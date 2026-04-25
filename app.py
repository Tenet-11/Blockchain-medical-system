from flask import Flask, request, jsonify
from blockchain import *

app = Flask(__name__)

# =========================
# 初始化 API 系統
# =========================
init_db()
reset_database()   # ← 加這行
blockchain = Blockchain()


def initialize_demo_data():
    """
    建立 API demo 用的初始病歷資料。
    注意：這裡只新增資料，不做 tampering。
    """
    record1 = MedicalRecord("R001", "P001", "Dr. Wang", "Flu", "Medicine A")
    record2 = MedicalRecord("R002", "P002", "Dr. Lin", "Cold", "Medicine B")
    record3 = MedicalRecord("R003", "P003", "Dr. Chen", "Fever", "Medicine C")

    insert_record(record1)
    insert_record(record2)
    insert_record(record3)

    blockchain.add_block(record1)
    blockchain.add_block(record2)
    blockchain.add_block(record3)


initialize_demo_data()


# =========================
# API 1：新增病歷資料
# =========================
@app.route("/records", methods=["POST"])
def add_record():
    data = request.json

    record = MedicalRecord(
        data["record_id"],
        data["patient_id"],
        data["doctor_name"],
        data["diagnosis"],
        data["prescription"]
    )

    insert_record(record)
    blockchain.add_block(record)

    return jsonify({
        "message": "Record added successfully",
        "record_id": record.record_id
    })


# =========================
# API 2：查詢全部病歷
# =========================
@app.route("/records", methods=["GET"])
def get_records():
    records = get_all_records()

    result = []
    for r in records:
        result.append({
            "record_id": r[0],
            "patient_id": r[1],
            "doctor_name": r[2],
            "diagnosis": r[3],
            "prescription": r[4],
            "timestamp": r[5],
            "hash": r[6]
        })

    return jsonify(result)


# =========================
# API 3：查詢單筆病歷
# =========================
@app.route("/records/<record_id>", methods=["GET"])
def get_record(record_id):
    r = get_record_by_id(record_id)

    if not r:
        return jsonify({"error": "Record not found"}), 404

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
# API 4：驗證病歷完整性
# =========================
@app.route("/verify/<record_id>", methods=["GET"])
def verify(record_id):
    result = verify_record_from_db(record_id, blockchain)

    return jsonify({
        "record_id": record_id,
        "result": "VALID" if result else "INVALID"
    })


# =========================
# API 5：模擬資料竄改 Demo
# =========================
@app.route("/tamper/<record_id>", methods=["POST"])
def tamper(record_id):
    tamper_database_record(record_id, "Cancer")

    return jsonify({
        "message": "Database record has been tampered",
        "record_id": record_id,
        "new_diagnosis": "Cancer"
    })


# =========================
# 啟動 Flask API Server
# =========================
if __name__ == "__main__":
    app.run(debug=False)