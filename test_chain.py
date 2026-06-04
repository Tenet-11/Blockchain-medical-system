from datetime import datetime

from blockchain_contract import (
    store_hash_on_chain,
    get_hash_from_chain,
    verify_hash_on_chain,
    get_record_count_on_chain
)

suffix = datetime.now().strftime("%H%M%S")

record_id = "R" + suffix
patient_id = "P" + suffix
record_hash = "abc123testhash_" + suffix

print("Current record count:")
print(get_record_count_on_chain())

print("\nTest record:")
print("record_id:", record_id)
print("patient_id:", patient_id)
print("record_hash:", record_hash)

print("\nStoring hash on chain...")
result = store_hash_on_chain(record_id, patient_id, record_hash)
print(result)

print("\nGetting hash from chain...")
chain_data = get_hash_from_chain(record_id)
print(chain_data)

print("\nVerifying correct hash...")
is_valid = verify_hash_on_chain(record_id, record_hash)
print("Valid:", is_valid)

print("\nVerifying wrong hash...")
is_valid_wrong = verify_hash_on_chain(record_id, "wrong_hash")
print("Valid:", is_valid_wrong)

print("\nCurrent record count:")
print(get_record_count_on_chain())