from io import StringIO
import csv
from datetime import datetime

def anki_csv_bytes(language, cards):
   
    #  Build CSV bytes in format: Front,Back,Tags
    #  Front = term; Back = definition + example + QA
    #  Returns UTF-8 bytes (with BOM) so Excel handles non-English correctly.
   
    sio = StringIO()
    writer = csv.writer(sio, lineterminator="\n")
    writer.writerow(["Front", "Back", "Tags"])
    for c in cards or []:
        term = c.get("term", "")
        definition = c.get("definition", "")
        example = c.get("example", "")
        qa = c.get("qa", {}) if isinstance(c.get("qa", {}), dict) else {}
        q = qa.get("question", "")
        a = qa.get("answer", "")
        back = f"{definition}\n\nExample: {example}\nQ: {q}\nA: {a}"
        writer.writerow([term, back, language])
    return sio.getvalue().encode("utf-8-sig")

def pretty_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")
