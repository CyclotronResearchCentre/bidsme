from PyQt5.QtWidgets import QAbstractScrollArea, QSizePolicy

ROW_HEIGHT = 22

def set_table_default(table, minimum: bool=True):
    table.setAlternatingRowColors(False)
    table.setShowGrid(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
    table.setMinimumHeight(2 * (ROW_HEIGHT + 5))
    table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

    if minimum:
        table.setSizePolicy(QSizePolicy.Expanding, 
                            QSizePolicy.Minimum)
    else:
        table.setSizePolicy(QSizePolicy.Expanding, 
                            QSizePolicy.Expanding)
