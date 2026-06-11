from web3 import Web3

# =========================
# Ganache 設定
# =========================
GANACHE_URL = "http://127.0.0.1:7545"

CONTRACT_ADDRESS = "0x02109F466D00328d6F41Eef4ea51739ecE3aD6E7"

CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "string",
                "name": "recordId",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "patientId",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "recordHash",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "RecordHashStored",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_recordId",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_patientId",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_recordHash",
                "type": "string"
            }
        ],
        "name": "storeRecordHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getRecordCount",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_recordId",
                "type": "string"
            }
        ],
        "name": "getRecordHash",
        "outputs": [
            {
                "internalType": "string",
                "name": "recordId",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "patientId",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "recordHash",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            },
            {
                "internalType": "bool",
                "name": "exists",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "index",
                "type": "uint256"
            }
        ],
        "name": "getRecordIdByIndex",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_recordId",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_hashToVerify",
                "type": "string"
            }
        ],
        "name": "verifyRecordHash",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# =========================
# 連線到 Ganache
# =========================
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if w3.is_connected():
    print("[Blockchain] Connected to Ganache")
else:
    print("[Blockchain] Failed to connect to Ganache")

# Ganache 第一個帳戶
account = w3.eth.accounts[0]

# 建立合約物件
contract = w3.eth.contract(
    address=w3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI
)


# =========================
# 將 hash 存到區塊鏈
# =========================
def store_hash_on_chain(record_id, patient_id, record_hash):
    tx_hash = contract.functions.storeRecordHash(
        record_id,
        patient_id,
        record_hash
    ).transact({
        "from": account
    })

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "tx_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "status": receipt.status
    }


# =========================
# 從區塊鏈查詢 hash
# =========================
def get_hash_from_chain(record_id):
    result = contract.functions.getRecordHash(record_id).call()

    return {
        "record_id": result[0],
        "patient_id": result[1],
        "record_hash": result[2],
        "timestamp": result[3],
        "exists": result[4]
    }


# =========================
# 驗證目前 hash 是否和鏈上一樣
# =========================
def verify_hash_on_chain(record_id, current_hash):
    return contract.functions.verifyRecordHash(
        record_id,
        current_hash
    ).call()


# =========================
# 查目前鏈上總共有幾筆紀錄
# =========================
def get_record_count_on_chain():
    return contract.functions.getRecordCount().call()