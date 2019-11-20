import QtQuick 2.6
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.3

import "../common"
import "."

Item {
    id: selectTripScreen

    function page_state_id() { // for transitions
        return "logbook_fg_state";
    }

    property bool show_only_current: false  // show only current haul

    Component.onCompleted: {
        show_only_current = main.framFooter.logbook_list_mode === "Current Set";
    }

    Connections {
        target: main.framFooter
        onClickedCurrentHaul: {
            show_only_current = true;
        }
        onClickedTripHauls: {
            show_only_current = false;
        }
    }

    Connections {
        // Scroll svColumnTitles when svGridData is scrolled
        target: svGridData.flickableItem
        onContentXChanged: {
            svColumnTitles.flickableItem.contentX = svGridData.flickableItem.contentX;
        }
    }

    ScrollView {
        // controlled by svGridData
        id: svColumnTitles
        x: 0
        y: 0
        width: parent.width
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        verticalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        GridLayout {
            id: gridLogbook
            columns: 15 + appstate.sets.maxObsRetModelLength + appstate.sets.maxVesselRetModelLength
            columnSpacing: 0
            rowSpacing: 0


            LogbookCell {
                id: cellHaulLabel
                text: "Set"
            }
            LogbookCell {

            }
            LogbookCell {
                text: "Date"
                implicitWidth: 90
            }
            LogbookCell {
                text: "Time"
            }
            LogbookCell {
                text: "Lat\nDeg"
            }
            LogbookCell {
                text: "Lat\nMin"
            }
            LogbookCell {
                text: "Long\nDeg"
            }
            LogbookCell {
                text: "Long\nMin"
            }
            LogbookCell {
                text: "Ave\nDepth"
            }
            LogbookCell {
                text: "EFP?"
            }
            LogbookCell {
                text: "Gear\nType"
            }
            LogbookCell {
                text: "Target\nStrat"
            }
            LogbookCell {
                text: "Seabird\nDeter."
            }

            Repeater {
                model: appstate.sets.maxObsRetModelLength
                LogbookCell {
                    text: "Obs.\nRet"
                }
            }
        }
    }

    FramBigScrollView {
        id: svGridData
        width: parent.width
        y: gridLogbook.height
        height: parent.height - gridLogbook.height

        GridLayout {
            id: gridDataCells
            columns: 15 + appstate.sets.maxObsRetModelLength + appstate.sets.maxVesselRetModelLength
            columnSpacing: 0
            rowSpacing: 0

            // ------------ DATA CELLS -----------

            Repeater {
                id: rptData
                model: appstate.sets.SetsModel
                LogbookSetRow {
                    Layout.columnSpan: gridLogbook.columns
                    set_num: fishing_activity_num
                    set_db_id: fishing_activity
                    gear_type_num: gear_type ? gear_type : ""
                    target_strat: target_strategy_code ? target_strategy_code : ""
                    locationData: appstate.sets.SetsModel.getLocationData(fishing_activity)
                    is_efp: efp !== undefined ? ((!efp || efp == "FALSE") ? "N" : "Y") : "N"
                    //has_brd: brd_present !== undefined ? ((!brd_present || brd_present == "FALSE") ? "N" : "Y") : ""
                    seabird_deterrent: deterrent_used !== undefined ? ((deterrent_used == 0) ? "N" : "Y") : ""
                    onModelUpdated: {
                        locationData = appstate.sets.SetsModel.getLocationData(fishing_activity);
                    }                    
                    visible: (!show_only_current || index + 1 == rptData.count)
                }
            }
        }
    }

}
