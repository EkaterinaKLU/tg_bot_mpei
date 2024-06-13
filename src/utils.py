import datetime
import json
import os.path
import pathlib
import string
import uuid

import jsonlines

from settings import settings
from storage import storage
from models import QuestionsFineTuningForm, File


def gen_fine_tuning_file(questions: QuestionsFineTuningForm) -> File:
    file_path = os.path.join(settings.files_dir_path, str(uuid.uuid4()))

    data_to_fine_tune = {
        "ac_date_start": questions.ac_date_start.strftime("%Y.%m.%d"),
        "ac_date_end": questions.ac_date_end.strftime("%Y.%m.%d"),
        "od_date": questions.od_date.strftime("%Y.%m.%d %H:%M"),
        "doc_esys_date_start": questions.doc_esys_date_start.strftime("%Y.%m.%d"),
        "doc_ftf_date_start": questions.doc_ftf_date_start.strftime("%Y.%m.%d"),
        "od_address": questions.od_address,
        "fod": questions.fod,
    }
    with open(pathlib.Path(__file__).parent.resolve() / "template.json") as f:
        content = json.load(f)
    with jsonlines.open(file_path, "w") as f:
        for pair in content:
            answer = string.Template(pair["answer"]).substitute(data_to_fine_tune)
            d = {
                "request": [
                    {
                        "role": "system",
                        "text": "Твоя задача состоит в том, чтобы отвечать на вопросы абитуриентов, которые хотят "
                        "поступить в МЭИ.  Отвечай вежливо и старайся выдать информацию, только если знаешь "
                        "точную информацию.",
                    },
                    {"role": "user", "text": pair["question"]},
                ],
                "response": answer,
            }
            f.write(d)

    file = storage.insert_file(
        file_path, "gen.json", "application/json", int((datetime.datetime.now().timestamp() + 3600))
    )
    return file
