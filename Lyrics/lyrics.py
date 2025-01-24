import syncedlyrics
import re
import json


query = input("Enter Song Name")
lrc = syncedlyrics.search(query)


lines = lrc.split("\n")


json_data = []


pattern = r"\[(\d+:\d+\.\d+)\] (.+)"

for line in lines:
    match = re.match(pattern, line)
    if match:
        timestamp, text = match.groups()

        text = bytes(text, "utf-8").decode("unicode_escape")

        json_entry = {"time": timestamp, "lyrics": text}
        json_data.append(json_entry)


json_string = json.dumps(json_data, indent=4)


print(json_string)
