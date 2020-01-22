import os
import shutil
import logging
import pandas

import tools.exceptions as Error
from Modules.MRI.MRI import MRI

logger = logging.getLogger(__name__)

rawfolder = ""
bidsfolder = ""
participants_table = None
rec_path = ""
train = False


def InitEP(**kwargs):
    global rawfolder
    global bidsfolder
    global train
    rawfolder = kwargs["rawfolder"]
    bidsfolder = kwargs["bidsfolder"]
    train = kwargs.get("train", False)

    participants = os.path.join(rawfolder, "participants.tsv")
    if not os.path.isfile(participants):
        e = "participants.tsv not found in {}".format(rawfolder)
        logger.error(e)
        raise Error.PluginInitEP(e)

    global participants_table
    participants_table = pandas.read_csv(participants, sep='\t',
                                         header=0,
                                         index_col="participant_id",
                                         na_values="n/a")

    participants_table = participants_table.groupby("participant_id")\
        .ffill().drop_duplicates()
    duplicates = participants_table.index.duplicated(keep=False)
    if duplicates.any():
        logger.error("One or several subjects have conflicting values."
                     "See {} for details"
                     .format(participants))
        raise Error.PluginInitEP("Conflicting values in subject descriptions")
    MRI.sub_BIDSfields.LoadDefinitions(os.path.join(rawfolder, 
                                                    "participants.json"))

def SessionEP(recording):
    if train:
        return 0

    sub = recording.sub_BIDSvalues["participant_id"]
    part = participants_table.loc[sub]
    for f in participants_table.columns:
        recording.sub_BIDSvalues[f] = part[f]

    # copytng behevioral data
    sub = recording.getSubId()
    ses = recording.getSesId()
    aux_input = os.path.join(rawfolder, sub, ses, "aux")
    if ses in ("ses-LCL", "ses-HCL"):
        if not os.path.isdir(aux_input):
            logger.error("Session {}/{} do not contain aux folder"
                         .format(sub, ses))
            raise Error.PluginSessionEP("folder {} not found"
                                        .format(aux_input))
        beh = os.path.join(bidsfolder, sub, ses, "beh")
        os.makedirs(beh, exist_ok=True)

        shutil.copy2("{}/{}.tsv".format(aux_input, "FCsepNBack"),
                     "{}/{}_{}_task-nBack_events.tsv"
                     .format(beh, sub, ses)
                     )
        shutil.copy2("{}/{}.json".format(aux_input, "FCsepNBack"),
                     "{}/{}_{}_task-nBack_events.json"
                     .format(beh, sub, ses)
                     )
        shutil.copy2("{}/{}.tsv".format(aux_input, "Vas"),
                     "{}/{}_{}_task-nBack_beh.tsv"
                     .format(beh, sub, ses)
                     )
        shutil.copy2("{}/{}.json".format(aux_input, "Vas"),
                     "{}/{}_{}_task-nBack_beh.json"
                     .format(beh, sub, ses)
                     )

last_id = None
series_list = dict()

def RecordingEP(recording):
    path = recording.recPath()
    recno = recording.recNo()
    recid = recording.recId()
    serie = os.path.basename(path)

    global last_id
    global series_list
    global rec_path

    if rec_path != path:
        rec_path = path
        series_list = sorted(os.listdir(os.path.join(rec_path, '..')))

    index = series_list.index(serie)
    if index < 0:
        logger.error("{}: Unable to get index of current serie"
                     .format(recording.recIdentity()))
        raise IndexError("Unable to get index of current serie")
    if recid == "cmrr_mbep2d_bold_mb2_invertpe":
        mod = series_list[index + 1]
        if mod.endswith("cmrr_mbep2d_bold_mb2_task_fat"):
            recording.setAttribute("SeriesDescription", "nBack")
        elif mod.endswith("cmrr_mbep2d_bold_mb2_task_nfat"):
            recording.setAttribute("SeriesDescription", "nBack")
        elif mod.endswith("cmrr_mbep2d_bold_mb2_rest"):
            recording.setAttribute("SeriesDescription", "rest")
        else:
            recording.setAttribute("SeriesDescription", "invalid")
            logger.warning("{}: Unknown session {}"
                           .format(recording.recIdentity(),
                                   mod))
    elif recid == "gre_field_mapping":
        if recording.sesId() in ("ses-HCL", "ses-LCL"):
            recording.setAttribute("SeriesDescription", "HCL/LCL")
        elif recording.sesId() == "ses-STROOP":
            recording.setAttribute("SeriesDescription", "STROOP")
        else:
            logger.warning("{}: Unknown session {}"
                           .format(recording.recIdentity(),
                                   recording.sesId()))
            recording.setAttribute("SeriesDescription", "invalid")
    elif recid == "al_mtflash3d_sensArray":
        det = series_list[index + 2]
        if det.endswith("al_mtflash3d_PDw"):
            recording.setAttribute("SeriesDescription", "PDw")
        elif det.endswith("al_mtflash3d_T1w"):
            recording.setAttribute("SeriesDescription", "T1w")
        elif det.endswith("al_mtflash3d_MTw"):
            recording.setAttribute("SeriesDescription", "MTw")
        else:
            logger.warning("{}: Unable determine modality"
                           .format(recording.recIdentity()))
            recording.setAttribute("SeriesDescription", "invalid")
    elif recid == "al_mtflash3d_sensBody":
        det = series_list[index + 1]
        if det.endswith("al_mtflash3d_PDw"):
            recording.setAttribute("SeriesDescription", "PDw")
        elif det.endswith("al_mtflash3d_T1w"):
            recording.setAttribute("SeriesDescription", "T1w")
        elif det.endswith("al_mtflash3d_MTw"):
            recording.setAttribute("SeriesDescription", "MTw")
        else:
            logger.warning("{}: Unable determine modality"
                           .format(recording.recIdentity()))
            recording.setAttribute("SeriesDescription", "invalid")
