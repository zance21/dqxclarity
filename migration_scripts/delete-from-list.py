import os

files = [
    "00000012.json",
    "00000056.json",
]

for file in files:
    if os.path.exists(f"json/_lang/en/{file}"):
        os.remove(f"json/_lang/en/{file}")
    if os.path.exists(f"json/_lang/ja/{file}"):
        os.remove(f"json/_lang/ja/{file}")
