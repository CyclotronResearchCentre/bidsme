from . import exceptions

entry_points = {
        "InitEP": exceptions.InitEPError,
        "SubjectEP": exceptions.SubjectEPError,
        "SessionEP": exceptions.SessionEPError,
        "SequenceEP": exceptions.SequenceEPError,
        "RecordingEP": exceptions.RecordingEPError,
        "FileEP": exceptions.FileEPError,
        "SequenceEndEP": exceptions.SequenceEndEPError,
        "SessionEndEP": exceptions.SessionEndEPError,
        "FinaliseEP": exceptions.FinaliseEPError
        }
