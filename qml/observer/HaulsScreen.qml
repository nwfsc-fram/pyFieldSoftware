import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1

import "."
import "../common"

Item {
    id: haulsPage

    property bool clickDeleteMode: false  // click for delete haul

    function page_state_id() { // for transitions
        return "hauls_state";
    }

    function resetDelete() {
        clickDeleteMode = false;
        framFooter.resetDelete();
    }

    Timer {
        id: timerSelectNewest
        interval: 10
        repeat: false
        onTriggered: haulsTable.select_newest_haul()
    }

    ObserverTableView {
        id: haulsTable
        width: parent.width
        height: parent.height

        model: appstate.hauls.HaulsModel

        TableViewColumn {
            role: "fishing_activity_num"
            title: "Haul #"
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
                text: styleData ? (styleData.value ? styleData.value: "") : ""
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
            if (clickDeleteMode && appstate.hauls.HaulsModel.count > 0) {
                var haul_id = appstate.hauls.HaulsModel.get(row).fishing_activity;
                var haul_num = appstate.hauls.HaulsModel.get(row).fishing_activity_num;

                if (appstate.hauls.checkHaulEmpty(haul_id)) {
                    dlgConfirm.show("Are you sure you want to delete haul " + haul_num + "?",
                                    "delete_haul");
                } else {
                    dlgBadChoice.message = "Haul " + haul_num +
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

        function selectHaulId(haul_number) {
            // haul_number == fishing_activity_num
            console.log('Selected fishing_activity_num # ' + haul_number)
            selection.select(currentRow);
            appstate.hauls.currentHaulId = haul_number;
            catchCategory.currentHaulId = haul_number;
            if (!stackView.busy) {
                stackView.push(Qt.resolvedUrl("HaulDetailsScreen.qml")) // 4 pages
                obsSM.state_change("haul_details_state")
            }
        }

        function select_newest_haul() { // called by timer, to allow model to update
            haulsTable.currentRow = haulsTable.rowCount - 1;
            console.log('Select newest haul row: ' + haulsTable.currentRow)
            activateRowSelected();
        }

        Connections {
            target: framFooter
            onClickedLogbook: {
                if (!stackView.busy) {
                    stackView.push(Qt.resolvedUrl("LogbookScreen.qml"))
                    obsSM.state_change("logbook_state")
                }
            }
            onClickedDelete: {
                haulsPage.clickDeleteMode = true;
            }
        }

        Connections {
            target: framHeader
            onForwardClicked: {  // Moved out of Footer
                if (text_clicked === "Add Haul") {
                    if (appstate.isGearTypeTrawl) {
                        var new_haul_num = 1;
                        var newest_row = haulsTable.model.count - 1;
                        if (newest_row >= 0) {
                            new_haul_num = parseInt(haulsTable.model.get(newest_row).fishing_activity_num) + 1;
                        }
                        console.debug("Next Haul# = '" + new_haul_num + "'.");
                        // Pass parameter as string, the type of the database field.
                        appstate.hauls.create_haul('' + new_haul_num);  // slight delay until we can select it
                        timerSelectNewest.restart();
                    } else {
                        console.log("TODO SETS createNewSet() (currently Haul only)");
                    }
                }
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
            if (action_name == "delete_haul") {
                var haul_id = appstate.hauls.HaulsModel.get(haulsTable.currentRow).fishing_activity;
                appstate.hauls.deleteHaul(haul_id);
                resetDelete();
            }
        }
    }
}
