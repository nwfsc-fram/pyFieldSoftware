import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1

import "../common"
import "."

Item {
    id: selectTripScreen

    property bool clickDeleteMode: false  // click for delete trip

    function page_state_id() { // for transitions
        return "select_trip_state";
    }

    function resetDelete() {
        clickDeleteMode = false;
        observerFooterRow.resetDelete();
    }

    Connections {
        target: observerFooterRow
        onClickedNew: {
            if (appstate.trips.currentTrip) {
                dlgConfirm.show("Current trip is not ended.\nAre you sure you want to start a new trip?", "confirm_trip");
            } else {                
                to_trip_details_screen();
            }
        }
        onClickedDelete: {
            clickDeleteMode = true;
        }
    }

    Rectangle {
        id: backRect
        color: "lightgray"
        anchors.fill: parent
    }

    FramBigScrollView {
        id: scrollTrips
        anchors.fill: parent
        flickableItem.interactive: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        ObserverTableView {
            id: listTrips
            width: root.width
            height: root.height
            model: appstate.TripsModel
            TableViewColumn {
                role: "trip"
                title: "Trip #"
            }
            TableViewColumn {
                role: "vessel_name"
                title: "Vessel"
                delegate: Text {
                    text: model ? model.vessel_name : ""
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20
                }
            }
            TableViewColumn {
                role: "departure_date"
                title: "Departure Date"
                width: 200
                delegate: Text {
                    text: model && model.departure_date ? model.departure_date : "Not Started"

                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20
                }
            }
            TableViewColumn {
                role: "return_date"
                title: "Return Date"
                width: 200
                delegate: Text {
                    text: model && model.return_date ? model.return_date : "Not Ended"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20
                }
            }
            TableViewColumn {
                role: "user_name"
                title: "User"
                width: 200
                visible: appstate.trips.debrieferMode
                delegate: Text {
                    text: model ? model.user_name : ""
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 20
                }
            }
            onClicked: {
                if (clickDeleteMode) {
                    var trip_id = appstate.TripsModel.get(row).trip;
                    if (appstate.currentTripId === trip_id) {
                        dlgBadChoice.message = "Cannot delete currently selected trip.\nPlease change trips first.";
                        dlgBadChoice.open()
                        selectTripScreen.resetDelete();
                        return;
                    }

                    if (appstate.trips.checkTripEmpty(trip_id)) {
                        dlgConfirm.show("Are you sure you want to delete trip " + trip_id + "?",
                                        "delete_trip");
                    } else {
                        dlgBadChoice.message = "Trip " + trip_id +
                                " has haul data associated with it, cannot delete.";
                        dlgBadChoice.open();
                        selectTripScreen.resetDelete();
                        return;
                    }
                } else {
                    appstate.currentTripId = appstate.TripsModel.get(row).trip;
                    db_sync.markTripInProgress(appstate.currentTripId);
                    obsSM.to_previous_state();
                    stackView.pop();
                }
            }
        }
    }
    function to_trip_details_screen() {
        obsSM.to_previous_state();
        stackView.pop();
        if (appstate.isFixedGear) {
            obsSM.state_change("start_fg_state");
            stackView.push(Qt.resolvedUrl("TripDetailsFGScreen.qml"));
        } else {
            obsSM.state_change("start_trawl_state");
            stackView.push(Qt.resolvedUrl("TripDetailsScreen.qml"));
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
            if (action_name == "confirm_trip") {
                appstate.end_trip();
                parent.to_trip_details_screen();
            } else if (action_name == "delete_trip") {
                var trip_id = appstate.TripsModel.get(listTrips.currentRow).trip;
                appstate.trips.deleteTrip(trip_id)
                obsSM.to_previous_state();
                stackView.pop();
            }
        }
    }    
}
