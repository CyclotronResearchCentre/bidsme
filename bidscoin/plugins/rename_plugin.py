import os
import pandas
import glob
import logging

from tools import tools 
from bidsMeta import BIDSfieldLibrary

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

sub_columns = BIDSfieldLibrary()
sub_columns.AddField(
        name="participant_id",
        longName="Participant Id",
        description="label identifying a particular subject")
sub_columns.AddField(
    name="age",
    longName="Age",
    description="Age of a subject",
    units="year")
sub_columns.AddField(
    name="sex",
    longName="Sex",
    description="Sex of a subject",
    levels={
        "F"   : "Female",
        "M"   : "Male"}
        )
sub_columns.AddField(
        name="score",
        longName="Mental score",
        description="Mental score of subject")
sub_columns.AddField(
        name="group",
        longName="group",
        description="Group subject belongs",
        levels={"patient": "patient", "control": "control"})
sub_columns.AddField(
        name="paired",
        longName="Paired Id",
        description="Subject Id paired with this subject")
sub_columns.AddField(
        name="ses_1",
        longName="First session",
        description="Id of the first session taken by subject",
        levels={"ses-LCL": "Low charge level",
                "ses-HCL": "High charge level",
                "ses-STROOP": "Multiparametric scan"},
        )
sub_columns.AddField(
        name="ses_2",
        longName="Second session",
        description="Id of the second session taken by subject",
        levels={"ses-LCL": "Low charge level",
                "ses-HCL": "High charge level",
                "ses-STROOP": "Multiparametric scan"},
        )
sub_columns.AddField(
        name="ses_3",
        longName="Third session",
        description="Id of the second session taken by subject",
        levels={"ses-LCL": "Low charge level",
                "ses-HCL": "High charge level",
                "ses-STROOP": "Multiparametric scan"},
        )

kss_columns = BIDSfieldLibrary()
kss_columns.AddField("trial_type", "Asked question", 
                     "State evaluation question",
                     {"Motivation": "Estimation of motivation",
                      "Happiness": "Estimation of happiness",
                      "Fatigue": "Estimation of fatigue",
                      "Openness": "Estimation of openness",
                      "Stress": "Estimation of stress",
                      "Anxiety": "Estimation of anxiety",
                      "Effort": "Estimation of effort",
                      }
                     )
kss_columns.AddField("stim_file", "Image presented during question")
kss_columns.AddField("value", "Recieved estimation value")
kss_columns.AddField("value_percent", "Recieved estimation value "
                     "(as percentage)")
kss_columns.AddField("value_steps", "Recieved estimation value "
                     "(as number of steps)")

kss_questions = {"1": "Motivation",
                 "2": "Happiness",
                 "3": "Fatigue",
                 "4": "Openness",
                 "5": "Stress",
                 "6": "Anxiety",
                 "7": "Effort"}

kss_step = 0.15
kss_max = 4.95

FCsepNBack_columns = BIDSfieldLibrary()
FCsepNBack_columns.AddField("onset", "Onset (in seconds) of the event",
                            "Onset (in seconds) of the event measured "
                            "from the beginning of the acquisition of "
                            "the first volume in the corresponding task "
                            "imaging data file.",
                            units="s")
FCsepNBack_columns.AddField("duration", "Time that stimulus was presented",
                            units="s")
# FCsepNBack_columns.AddField("cond_duration", "Time that the condition was "
#                             "presented",
#                              units="s")
# FCsepNBack_columns.AddField("isi_duration", "Time that cross was presented",
#                             units="s")
FCsepNBack_columns.AddField("response_time", "Time taked to respond to "
                            "stimulus",
                            units="s")
FCsepNBack_columns.AddField("trial_type", "Condition presented to subject",
                            levels={"Test_1Back": "",
                                    "Test_2Back": "",
                                    "Test_3Back": ""}
                            )
FCsepNBack_columns.AddField("block", "Id of block for trial")
FCsepNBack_columns.AddField("value", "Recieved responce",
                            levels={"c":"correct",
                                    "n":"non correct"})
FCsepNBack_columns.AddField("exp_value", "Expected responce",
                            levels={"c":"correct",
                                    "n":"non correct"})


def InitEP(**kwargs):
    global source
    global destination
    global subject_file

    source = kwargs["source"]
    destination = kwargs["destination"]

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
    line = df_subjects.loc[index, prefix + "_sae"].split("_")
    sex = line[0]
    age = int(line[1])
    E = int(line[2])
    values = sub_columns.GetTemplate()
    values["participant_id"] = "sub-" + session["subject"]
    values["sex"] = sex
    values["age"] = age
    values["score"] = E

    if status == 0:
        values["group"] = "patient"
        values["paired"] = "sub-{:03}".format(int(df_subjects
                                                  .loc[index, "cnt"]))
    else:
        values["group"] = "control"
        values["paired"] = "sub-{:03}".format(int(df_subjects
                                                  .loc[index, "pat"]))
    values["ses_1"] = "ses-{}".format(df_subjects.loc[index, prefix + "_1"])
    values["ses_2"] = "ses-{}".format(df_subjects.loc[index, prefix + "_2"])
    values["ses_3"] = "ses-{}".format(df_subjects.loc[index, prefix + "_3"])

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
            f.write(sub_columns.GetHeader())
            f.write("\n")
    with open(os.path.join(destination, "participants.tsv"), "a") as f:
        f.write(sub_columns.GetLine(values))
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
    if len(task_fl) != 1:
        logger.error("Found {}  FCsepNBack log files")
        raise ValueError
    with open(task_fl[0], 'r', encoding="cp1252") as ifile,\
            open(aux_d + "/FCsepNBack.tsv", 'w') as ofile:
        ofile.write(FCsepNBack_columns.GetHeader())
        ofile.write('\n')
        t_offset = None
        values = FCsepNBack_columns.GetTemplate()
        for i, line in enumerate(ifile):
            if line[0] == "*":
                logger.warning("{}:{} Special line: '{}'"
                               .format(ifile.name, i, line))
                continue
            t, dt, evt = parce_logline(line)
            if t: 
                devt = parce_event(evt)
                if "COGENT START" in devt:
                    logger.debug("{}:{} Starting new COGENT session"
                                 .format(ifile, i))
                    if t_offset is not None:
                        logger.error("{}:{} Multiple sessions recorded "
                                     "in same log"
                                     .format(ifile.name, i))
                        raise ValueError
                if t_offset is None:
                    if evt[0] == "Key" and evt[1] == '20':
                        t_offset = int(evt[4])
                    continue

                if "ISI_Start_Bloc:" in devt:
                    if devt["ISI_Start_Bloc:"] in ('X','Y','Z'):
                        continue
                    values["block"] = devt["ISI_Start_Bloc:"]
                    values["trial_type"] = devt["ISICondition:"]
                    continue
                if values["block"] is None:
                    continue
                if "Bloc:" in devt:
                    values["onset"] = devt["Presenting at time:"]
                    if devt["Bloc:"] != values["block"]:
                        logger.error("{}:{} Incorrect block number {}"
                                     .format(ifile.name, i, devt["Bloc:"]))
                    if devt["Reponse fournie:"] == 14:
                        values["value"] = "c"
                        values["response_time"] = devt["Response at time:"] \
                            - values["onset"]
                    elif devt["Reponse fournie:"] == 23:
                        values["value"] = "n"
                        values["response_time"] = devt["Response at time:"] \
                            - values["onset"]
                    elif devt["Reponse fournie:"] in ("NA","NR"):
                        values["value"] = None
                        values["response_time"] = None
                    else:
                        logger.warning("{}:{} Unexpected responce: {}"
                                       .format(ifile.name, i,
                                               devt["Reponse fournie:"]))
                        values["response_time"] = None
                        values["value"] = None
                    values["exp_value"] = devt["Reponse attendue:"]
                elif "ISIBloc:" in devt:
                    if values["onset"] is None:
                        logger.warning("{}:{} ISIBloc with undefined "
                                       "onset time"
                                       .format(ifile.name, i))
                        continue
                    if values["value"] is None:
                        if devt["ISIReponse fournie:"] == 14:
                            values["value"] = "c"
                            values["response_time"] \
                                = devt["ISIResponse at time:"] \
                                - values["onset"]
                        elif devt["ISIReponse fournie:"] == 23:
                            values["value"] = "n"
                            values["ISIresponse_time"] \
                                = devt["ISIResponse at time:"] \
                                - values["onset"]
                        elif devt["ISIReponse fournie:"] in ("NA","NR"):
                            values["value"] = None
                        else:
                            logger.warning("{}:{} Unexpected responce: {}"
                                           .format(ifile.name, i,
                                                   devt["ISIReponse fournie:"])
                                           )
                            values["response_time"] = None
                            values["value"] = None
                        if values["exp_value"] is None:
                            values["exp_value"] = devt["ISIReponse attendue:"]

                    values["duration"] = devt["ISIPresenting at time:"] \
                        - values["onset"]
                    values["onset"] -= t_offset
                    for field in ("onset", "duration", "response_time"):
                        if values[field]:
                            values[field] = round(values[field] * 10e-6, 7)
                    ofile.write(FCsepNBack_columns.GetLine(values))
                    ofile.write('\n')

                    if values["onset"] < 0:
                        logger.warning("{}:{} Negative offset {}"
                                       .format(ifile.name, i, values["onset"]))
                    values["onset"] = None

        FCsepNBack_columns.DumpDefinitions(tools.change_ext(ofile.name,
                                                            "json"))

    # KSS log file
    # KSS_Vas_003_2.log
    kss_fl = glob.glob(logs + "/KSS_Vas*.log")
    if len(kss_fl) != 1:
        logger.error("Found {} KSS_Vas log files")
        raise ValueError
    with open(kss_fl[0], 'r', encoding="cp1252") as ifile,\
            open(aux_d + "/KSS.tsv", 'w') as ofile:
        ofile.write(kss_columns.GetHeader())
        ofile.write('\n')
        for line in ifile:
            if line[0] == "*":
                logger.warning("{}:{} Special line: '{}'"
                               .format(ifile.name, i, line))
                continue
            t, dt, evt = parce_logline(line)
            if t and evt[0] == "question":
                values = kss_columns.GetTemplate()
                values["trial_type"] = kss_questions[evt[1]]
                values["stim_file"] = "KSS/images/" + evt[3]
                v = float(evt[6])
                values["value"] = v
                values["value_percent"] = round(100 * (v / kss_max),2)
                values["value_steps"] = int(v // kss_step)
                ofile.write(kss_columns.GetLine(values))
                ofile.write('\n')
        kss_columns.DumpDefinitions(tools.change_ext(ofile.name, "json"))

    return 0


# def FileEP(session, path, recording):
#     pass


def parce_logline(line, split=None):
    li = line.split(split)
    if len(li) < 3 or li[2] != ":":
        return None, None, [line.strip()]

    t = float(li[0]) * 1e-6
    dt = float(li[1][1:-1]) * 1e-6
    txt = li[3:]
    txt = [evt.strip() for evt in txt]
    return t, dt, txt


def parce_event(event, cls=int):
    res = dict()
    tag = ""
    value = None
    for f in event:
        if tag.endswith(":"):
            if f == '/':
                value = None
            else:
                try:
                    value = cls(f)
                except ValueError:
                    value = f
            res[tag] = value
            tag = ""
            value = None
        elif tag:
            tag = tag + " " + f
        else:
            tag = f

    if tag != "":
        res[tag] = value

    return res
