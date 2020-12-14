import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1

import "."
import "../common"

Item {
    id: setsPage

    property bool clickDeleteMode: false  // click for delete haul

    function page_state_id() { // for transitions
        return "sets_state";
    }

    function resetDelete() {
        clickDeleteMode = false;
        framFooter.resetDelete();
    }

    Timer {
        id: timerSelectNewest
        interval: 10
        repeat: false
        onTriggered: setsTable.select_newest_set()
    }

    ObserverTableView {
        id: setsTable
        width: parent.width
        height: parent.height

        model: appstate.sets.SetsModel

        TableViewColumn {
            role: "fishing_activity_num"
            title: "Set #"
            width: 100
        }
        TableViewColumn {
            role: "otc_weight_method"
            title: "WM"
            width: 70
        }
        TableViewColumn {
            role: "gear_performance"
            title: "Gear Perf."
        }
        TableViewColumn {
            role: "target_strategy_code"
            title: "Target Strat."
        }
        TableViewColumn {
            role: "gear_type"
            title: "Gear Type"
            width: 120
        }
        TableViewColumn {
            role: "location_start_end"
            title: "Location (Start, End)"
            width: 250
        }

        TableViewColumn {
            role: "observer_total_catch"
            title: "OTC WT"
            width: 100
            delegate: Text {
                text: styleData ? (styleData.value ? styleData.value.toFixed(2): (styleData.value == 0 ? "0.0": "")) : ""  // show 0 as 0.0
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        }
        TableViewColumn {
            role: "errors"
            title: "Errors"
            width: 150
        }


        onClicked: {
            if (clickDeleteMode && appstate.sets.SetsModel.count > 0) {
                var set_id = appstate.sets.SetsModel.get(row).fishing_activity;
                var set_num = appstate.sets.SetsModel.get(row).fishing_activity_num;

                if (appstate.sets.checkSetEmpty(set_id)) {
                    dlgConfirm.show("Are you sure you want to delete set " + set_num + "?",
                                    "delete_set");
                } else {
                    dlgBadChoice.message = "Set " + set_num +
                            " has existing catch data associated with it.\n Cannot delete.";
                    dlgBadChoice.open();
                    resetDelete();
                }
            } else {
                activateRowSelected();
            }
        }

//        onCurrentRowChanged: {
//            activateRowSelected();
//        }

        function activateRowSelected() {
            if (clickDeleteMode) {
                return;
            }

            var haul_number = model.get(currentRow).fishing_activity_num;
            console.debug("Hauls row activated: " + currentRow + ", #: " + haul_number);
            selectHaulId(haul_number);
        }

        function selectHaulId(set_number) {
            console.log('Selected fishing_activity_num # ' + set_number)
            selection.select(currentRow);
            appstate.sets.currentSetId = set_number;
            catchCategory.currentHaulId = set_number;
            if (!stackView.busy) {
                stackView.push(Qt.resolvedUrl("SetDetailsScreen.qml")) // 4 pages
                obsSM.state_change("set_details_state")
            }
        }

        function select_newest_set() { // called by timer, to allow model to update
            setsTable.currentRow = setsTable.rowCount - 1;
            console.log('Select newest set row: ' + setsTable.currentRow)
            activateRowSelected();
        }

        Connections {
            target: framFooter
            onClickedLogbook: {
                if (!stackView.busy) {
                    stackView.push(Qt.resolvedUrl("LogbookFGScreen.qml"))
                    obsSM.state_change("logbook_fg_state")
                }
            }
            onClickedDelete: {
                setsPage.clickDeleteMode = true;
            }
        }

        Connections {
            target: framHeader
            onForwardClicked: {
                if (text_clicked === "Add Set") {
                    var new_set_num = 1;
                    var newest_row = setsTable.model.count - 1;
                    if (newest_row >= 0) {
                        new_set_num = parseInt(setsTable.model.get(newest_row).fishing_activity_num) + 1;
                    }
                    console.debug("Next Set# = '" + new_set_num + "'.");
                    // Pass parameter as string, the type of the database field.
                    appstate.sets.createSet('' + new_set_num);  // slight delay until we can select it
                    timerSelectNewest.restart();
                }
            }
        }
        Connections {
            target: appstate.catches
            onOtcFGWeightChanged: {
                appstate.sets.updateModelOTC(otc_fg, fishing_activity_num);
            }
        }
    }

    TrawlOkayDialog {
        id: dlgBadChoice
    }

    FramConfirmDialog {
        id: dlgConfirm
        auto_label: false
        y: 100
        onConfirmed: {
            if (action_name == "delete_set") {
                var set_id = appstate.sets.SetsModel.get(setsTable.currentRow).fishing_activity;
                appstate.sets.deleteSet(set_id);
                resetDelete();
            }
        }
    }
}
