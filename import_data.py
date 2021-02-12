import os
import json
import data

os.makedirs("data", exist_ok=True)

with open("data/goals.json", "w") as f:
    icons = {"travel": "⛱",
             "study": "🏫",
             "work": "🏢",
             "relocate": "🚜"}
    goals = {k: [v, icons[k]] for k, v in data.goals.items()}
    json.dump(goals, f, indent=4, ensure_ascii=False)

with open("data/teachers.json", "w") as f:
    json.dump(data.teachers, f, indent=4, ensure_ascii=False)
