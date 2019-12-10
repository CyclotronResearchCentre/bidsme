import os
import pandas
import glob
import shutil

import bids
from tools import tools 
import logging

logger = logging.getLogger(__name__)

source = None
destination = None
df_subjects = None

excel_col_list = {'Patient' : 'pat',
                  'S_A_E' : "pat_sae",
                  1: "pat_1", 2: "pat_2", 3: "pat_3",
                  'Contrôle' : "cnt",
                  'S_A_E.1': "cnt_sae",
                  '1.1': "cnt_1", '2.1': "cnt_2", '3.1': "cnt_3",
                  }


def InitEP(**kwargs):
    global source
    global destination
    global subject_file

    source = kwargs["source"]
    destination = kwargs["source"]

    if "subjects" in kwargs:
        subject_file = kwargs["subjects"]
    else:
        subject_file = os.path.join(source, "Appariement.xlsx")
    if not os.path.isfile(subject_file):
        raise FileNotFoundError(str(subject_file))


def SubjectEP(session):
    global df_subjects

    if df_subjects is None:
        df_subjects = pandas.read_excel(subject_file,
                                        sheet_name=0, header=0,
                                        usecols=[0,1,2,3,4,5,6,7,8,9,10])
        df_subjects.rename(index=str, columns=excel_col_list,inplace=True)
        df_subjects = df_subjects[df_subjects['pat'].notnull()
                                  | df_subjects['cnt'].notnull()]

    # looking for subject in table
    sub_id = int(session["subject"])
    index = df_subjects.loc[df_subjects["pat"] == sub_id].index 
    status = 0
    prefix = "pat"
    if len(index) == 0:
        index = df_subjects.loc[df_subjects["cnt"] == sub_id].index
        if len(index) == 0:
            raise Exception("Subject {} not found in table"
                            .format(sub_id))
            status = 1
            prefix = "cnt"
    index = index[0]
    l = df_subjects.loc[index, prefix + "_sae"].split("_")
    sex = l[0]
    age = int(l[1])
    E = int(l[2])

    line = ["n/a"] * 9
    line[0] = "sub-" + session["subject"]
    line[1] = l[0]
    line[2] = l[1]
    line[3] = l[2]
    if status == 0:
        line[4] = "patient"
        line[5] = "sub-{:03}".format(int(df_subjects.loc[index, "cnt"]))
    else:
        line[4] = "control"
        line[5] = "sub-{:03}".format(int(df_subjects.loc[index, "pat"]))
    line[6] = "ses-{}".format(df_subjects.loc[index, prefix + "_1"])
    line[7] = "ses-{}".format(df_subjects.loc[index, prefix + "_2"])
    line[8] = "ses-{}".format(df_subjects.loc[index, prefix + "_3"])

    ses = sorted([os.path.basename(s) for s in 
                  tools.lsdirs(os.path.join(source, session["subject"]))
                  ])
    scans = df_subjects.loc[index, prefix + "_1":prefix + "_3"].to_list()
    session["scans"] = dict()
    for name, scan in zip(scans, ses):
        session["scans"][scan] = name

    # creating tsv file
    tsv_file = os.path.join(destination, "participants.tsv")
    if not os.path.isfile(tsv_file):
        with open(tsv_file, 'w') as f:
            f.write("\t".join(("participant_id",
                               "sex",
                               "age",
                               "score",
                               "group",
                               "paired",
                               "ses_1",
                               "ses_2",
                               "ses_3")
                              )
                    )
            f.write("\n")
    with open(os.path.join(destination, "participants.tsv"), "a") as f:
        f.write("\t".join(line))
        f.write("\n")

    return 0


def SessionEP(session):
    session["session"] = session["scans"][session["session"]]


def RecordingEP(session, recording):
    if session["session"] == "STROOP":
        return 0

    logs = os.path.dirname(recording.rec_path) + "/inp"
    if not os.path.isdir(logs):
        raise NotADirectoryError(logs)

    aux_d = os.path.join(session["path"], "aux")
    if not os.path.isdir(aux_d):
        os.makedirs(aux_d)

    # Task log file
    # FCsepNBack_003_1.log
    task_fl = glob.glob(logs + "/FCsepNBack*.log")
    for file in task_fl:
        shutil.copy(file, aux_d)

    # KSS log file
    # KSS_Vas_003_2.log
    kss_fl = glob.glob(logs + "/KSS_Vas*.log")
    for file in kss_fl:
        shutil.copy(file, aux_d)

    return 0


# def FileEP(session, path, recording):
#     pass
