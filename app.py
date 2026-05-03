# 從 flask 套件引入：
# Flask → 建立伺服器
# request → 取得使用者傳來的資料（例如 POST JSON）
# jsonify → 回傳 JSON 格式資料
from flask import Flask, request, jsonify

# 從你自己寫的 blockchain.py 匯入所有功能
from blockchain import *

# 建立 Flask 應用（server）
app = Flask(__name__)


# =========================
# 初始化 API 系統
# =========================

# 建立資料庫（如果不存在）
init_db()

# 清空資料庫（讓 demo 每次都是乾淨狀態）
reset_database()

# 建立區塊鏈物件（存在記憶體中）
blockchain = Blockchain()


def initialize_demo_data():
    """
    建立三筆測試用的醫療資料
    """

    # 建立 MedicalRecord 物件（類似 struct / class instance）
    record1 = MedicalRecord("R001", "P001", "Dr. Wang", "Flu", "Medicine A")
    record2 = MedicalRecord("R002", "P002", "Dr. Lin", "Cold", "Medicine B")
    record3 = MedicalRecord("R003", "P003", "Dr. Chen", "Fever", "Medicine C")

    # Python 語法：for loop + list
    # 依序處理每一筆資料
    for record in [record1, record2, record3]:
        insert_record(record)        # 存進 SQLite（DB）
        blockchain.add_block(record) # 存進區塊鏈


# 呼叫函式（程式啟動時就會執行）
initialize_demo_data()


# =========================
# API 1：查詢全部病歷
# =========================

# @app.route = Flask 的「路由」
# 當有人用 GET 請求 /records，就會執行這個函式
@app.route("/records", methods=["GET"])
def get_records():

    # 從 DB 拿所有資料（回傳 list）
    records = get_all_records()

    result = []

    # r 是 tuple，例如：
    # ("R001", "P001", "Dr. Wang", ...)
    for r in records:

        # 把 tuple 轉成 dictionary（JSON 格式）
        result.append({
            "record_id": r[0],
            "patient_id": r[1],
            "doctor_name": r[2],
            "diagnosis": r[3],
            "prescription": r[4],
            "timestamp": r[5],
            "hash": r[6]
        })

    # jsonify 會自動轉成 JSON 回傳給前端
    return jsonify(result)


# =========================
# API 2：查詢單筆病歷
# =========================

# <record_id> 是「路徑參數」
# 例如 /records/R002 → record_id = "R002"
@app.route("/records/<record_id>", methods=["GET"])
def get_record(record_id):

    # 從 DB 找指定 record
    r = get_record_by_id(record_id)

    # 如果找不到 → 回傳錯誤
    if not r:
        return jsonify({"error": "Record not found"}), 404

    # 回傳該筆資料
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
# =========================

# POST 通常用來「新增資料」
@app.route("/records", methods=["POST"])
def add_record():

    # request.json → 取得使用者傳來的 JSON
    # 例如：
    # {
    #   "record_id": "R004",
    #   ...
    # }
    data = request.json

    # 建立 MedicalRecord 物件
    record = MedicalRecord(
        data["record_id"],
        data["patient_id"],
        data["doctor_name"],
        data["diagnosis"],
        data["prescription"]
    )

    # 存進 DB
    insert_record(record)

    # 加進區塊鏈
    blockchain.add_block(record)

    # 回傳成功訊息
    return jsonify({
        "message": "Record added successfully",
        "record_id": record.record_id
    })


# =========================
# API 4：驗證病歷完整性
# =========================

@app.route("/verify/<record_id>", methods=["GET"])
def verify(record_id):

    # 呼叫你在 blockchain.py 寫的驗證函式
    result = verify_record_from_db(record_id, blockchain)

    # 三元運算子（Python 簡寫 if-else）
    # True → VALID
    # False → INVALID
    return jsonify({
        "record_id": record_id,
        "result": "VALID" if result else "INVALID"
    })


# =========================
# API 5：模擬竄改資料
# =========================

@app.route("/tamper/<record_id>", methods=["GET"])
def tamper(record_id):

    # 把 diagnosis 改成 Cancer（模擬駭客）
    tamper_database_record(record_id, "Cancer")

    return jsonify({
        "message": "Database record has been tampered",
        "record_id": record_id,
        "new_diagnosis": "Cancer"
    })


# =========================
# 啟動 Flask Server
# =========================

# 只有「直接執行這個檔案」才會跑這段
if __name__ == "__main__":

    # debug=True：
    # - 自動重啟
    # - 顯示錯誤訊息
    app.run(debug=True)