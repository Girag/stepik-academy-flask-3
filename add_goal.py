import os
import json

if os.path.isfile("data/goals.json") and os.path.getsize("data/goals.json"):
    with open("data/goals.json", "r") as f:
        records = json.load(f)
    records.update({"programming": ["Для программирования", "👩‍💻"]})
    with open("data/goals.json", "w") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)
else:
    record = {"programming": ["Для программирования", "👩‍💻"]}
    with open("data/goals.json", "w") as f:
        json.dump(record, f, indent=4, ensure_ascii=False)

if os.path.isfile("data/teachers.json") and os.path.getsize("data/teachers.json"):
    with open("data/teachers.json", "r") as f:
        records = json.load(f)
    ids = (8, 9, 10, 11)
    for record in records:
        if record['id'] in ids:
            record['goals'].append("programming")
    with open("data/teachers.json", "w") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)
