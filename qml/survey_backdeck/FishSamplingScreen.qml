import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Window 2.2
import SortFilterProxyModel 0.1

import "../common"

Item {
    id: root
    property bool externalUpdate: false;
    property variant randomDrops: null;

    Connections {
        target: serialPortManager
        onExceptionEncountered: showException(comPort, msg);
    } // serialPortManager.onExceptionEncountered
    function showException(comPort, msg) {
        dlgOkay.width = 700;
        dlgOkay.height = 300;
        dlgOkay.message = msg;
        dlgOkay.action = "Please check Serial Port Manager"
        dlgOkay.open()
    }

    Connections {
        target: dlgFishSamplingEntry
        onSpecimenCleared: nextFishClicked();
    } // dlgFishSamplingEntry.specimenCleared
    function nextFishClicked() {
        console.info('nextFishClicked ...');
        if (tvSpecimens.currentRow !== -1) {
            externalUpdate = true; // Indicates that this was called by the FishSamplingEntryDialog
            tvSpecimens.selection.clear();
            stateMachine.angler = null;
            stateMachine.drop = null;
            stateMachine.hook = null;
            console.info('state machine adh: ' + stateMachine.angler + stateMachine.drop + stateMachine.hook);
//            tvSpecimens.selection.deselect(tvSpecimens.currentRow);
        }
    }

    Connections {
        target: fishSampling
        onSpecimenSelected: updateSelectedSpecimen(specimen);
    } // fishSampling.onSpecimenSelected
    function updateSelectedSpecimen(specimen) {
        console.info('updateSelectedSpecimen: ' + JSON.stringify(specimen));
        if (specimen['specimenID'] !== undefined) {
            var index = tvSpecimens.model.get_item_index("specimenID", specimen['specimenID']);
            if (index !== -1) {

                externalUpdate = true; // Sets whether the tvSpecimens was updated by clicked on the table
                  // or by an external process, i.e. by something happening in the FishSamplingEntryDialog.qml dialog

                // This clear is not needed as the selection is set below anyways
//                tvSpecimens.selection.clear();

//                console.info('\tCounts:  model=' + tvSpecimens.model.count + ', table=' + tvSpecimens.rowCount);
                tvSpecimens.__listView.positionViewAtIndex(index, ListView.End);
//                console.info('\tCounts after positioning:  model=' + tvSpecimens.model.count + ', table=' + tvSpecimens.rowCount);

                // Must do the selection.select(index) after the positionViewAtIndex, as this seems to force an
                // update to the tvSpecimens.rowCount value, for otherwise one gets an index out of range error with the
                // selection.select command
                tvSpecimens.selection.select(index);
                tvSpecimens.currentRow = index;
                var adh = tvSpecimens.model.get(index).adh;
                if ((adh !== undefined) && (adh.length === 3)) {
                    stateMachine.angler = adh.charAt(0);
                    stateMachine.drop = adh.charAt(1);
                    stateMachine.hook = adh.charAt(2);
                    console.info('state machine adh: ' + stateMachine.angler + stateMachine.drop + stateMachine.hook +
                       ', currentEntryTab: ' + stateMachine.currentEntryTab);
                }
            }
        }
    }

    function editSpecimen() {
        // Function called when a specimen row is double-clicked or the edit button is pressed
        if (tvSpecimens.currentRow !== -1) {
            var id = fishSampling.specimensModel.get(tvSpecimens.currentRow).specimenID;
            console.info('editSpecimen, specimenID: ' + id);
//            getCurrentIndex();
            if (id !== undefined) {
                dlgFishSamplingEntry.specimenID = id;
                // Retrieve the existing specimen data and populate the dialog
                fishSampling.selectSpecimenRecordByID(id);
                dlgFishSamplingEntry.title = "Fish Sampling Entry - Random Drops - " + fishSampling.randomDrops.join(', ');
                dlgFishSamplingEntry.open()
            }
        }
    }

    function getDispositionLabel(row, value) {
        if (row != -1) {
            var item = fishSampling.specimensModel.get(row);
            var disposition = item["disposition"];
            var dispositionType = item["dispositionType"];
//            console.info('disposition=' + disposition + ', type=' + dispositionType);
            dispositionType = (dispositionType !== undefined) ? dispositionType.substring(0,1) : ""
            disposition = (disposition !== undefined) ? disposition : ""
            return dispositionType + disposition;
        }
        return "";
    }

    ColumnLayout {
        id: clFishSampling
        spacing: 20
        anchors.fill: parent
        RowLayout {
            id: rlTopButtons
            spacing: 10
            anchors.top: parent.top
            anchors.topMargin: 10
            anchors.left: parent.left
            BackdeckButton {
                id: btnAddFish
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Add Fish")
                onClicked: {
                    dlgFishSamplingEntry.clearTabs();
                    dlgFishSamplingEntry.title = "Fish Sampling Entry - Random Drops - " + fishSampling.randomDrops.join(', ');
                    dlgFishSamplingEntry.open()
                }
            } // btnAddFish
            BackdeckButton {
                id: btnEditFish
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Edit Fish")
                state: tvSpecimens.currentRow !== -1 ? "enabled" : "disabled"
                onClicked: {
                    editSpecimen();
                }
            } // btnEditFish
            BackdeckButton {
                id: btnDeleteFish
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Delete Fish")
                state: tvSpecimens.currentRow !== -1 ? "enabled" : "disabled"
                onClicked: {
                    if (tvSpecimens.currentRow !== -1) {
                        var item = tvSpecimens.model.get(tvSpecimens.currentRow);
                        console.info('fish to delete:  row = ' + tvSpecimens.currentRow + ', item = '+ JSON.stringify(item));
                        dlgOkayCancel.message = "You are about to delete this specimen #" + item.ID;
                        dlgOkayCancel.action = "Do you wish to proceed?"
                        dlgOkayCancel.accepted_action = "delete specimen";
                        dlgOkayCancel.open();
                    }
                }
            } // btnDeleteFish
            Label { Layout.fillWidth: true }

//            BackdeckButton {
//                id: btnTestSerialPort
//                text: qsTr("Serial\nTest")
//                Layout.preferredWidth: 80
//                Layout.preferredHeight: 60
//                onClicked: {
//                    fishSampling.testSerialPort();
//                }
//            } // btnTestSerialPort

            BackdeckButton {
                id: btnFinished
                text: qsTr("Finished &\nValidate")
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                onClicked: {
                    smBackdeck.to_sites_state();
                    sites.finishedAndValidate();
                }
            } // btnFinished
            BackdeckButton {
                id: btnRecordedBy
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: ((stateMachine.recorder !== undefined) && (stateMachine.record !== null) & (stateMachine.recorder !== "")) ?
                    "Recorded By\n" + stateMachine.recorder.substring(0,11) :
                    "Recorded By"
                onClicked: {

//                    this.cursorShape = Qt.IBeamCursor;
//                    dlgRecordedBy.currentRecorder = stateMachine.recorder;
                    var index = fishSampling.personnelModel.get_item_index("displayText", stateMachine.recorder);
                    dlgRecordedBy.lvPersonnel.positionViewAtIndex(index, ListView.Center)
                    dlgRecordedBy.lvPersonnel.currentIndex = index;

                    dlgRecordedBy.open();
                }
//                state: "disabled"
            } // btnRecordedBy
            BackdeckButton {
                id: btnNotes
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Site Notes")
                onClicked: {
                    if (tvSpecimens.currentRow != -1) {
                        var item = fishSampling.specimensModel.get(tvSpecimens.currentRow);
                        var adh = item["adh"];
                        if (adh !== undefined) {
                            stateMachine.angler = adh[0].toUpperCase();
                            stateMachine.drop = adh[1];
                            stateMachine.hook = adh[2];
                        }
                    }
//                    dlgDrawingNotes.canvas.clear_canvas();
                    dlgDrawingNotes.open();
                    dlgDrawingNotes.canvas.clear_canvas();
                }
            } // btnNotes
            BackdeckButton {
                id: btnHome
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("<<")
                onClicked: {
                    smBackdeck.to_sites_state();
                }
            } // btnHome
        } // rlTopButtons
        BackdeckTableView {
            id: tvSpecimens
            Layout.preferredWidth: parent.width
            Layout.fillHeight: true
            selectionMode: SelectionMode.SingleSelection
            headerVisible: true
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

            model: fishSampling.specimensModel

            TableViewColumn {
                role: "ID"
                title: "ID"
                width: 50
            } // id
            TableViewColumn {
                role: "species"
                title: "Species"
                width: 220
                delegate: Text {
                    text: styleData.value ? styleData.value.substring(0, 21) : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // species
            TableViewColumn {
                role: "adh"
                title: "A-D-H"
                width: 80
                delegate: Text {
                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // adh
            TableViewColumn {
                role: "weight"
                title: "Weight"
                width: 80
                delegate: Text {
//                    text: (typeof styleData.value == 'number') ?
                    text: parseFloat(styleData.value) ? parseFloat(styleData.value).toFixed(2) : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // weight
            TableViewColumn {
                role: "length"
                title: "Len"
                width: 60
                delegate: Text {
                    text: parseFloat(styleData.value) ? parseFloat(styleData.value).toFixed(0) : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // length
            TableViewColumn {
                role: "sex"
                title: "Sex"
                width: 60
                delegate: Text {
                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // sex
            TableViewColumn {
                role: "ageID"
                title: "Age"
                width: 80
                delegate: Text {
//                    text: getAgeLabel(styleData.row, styleData.value);
                    text: styleData.value ? styleData.value : ""
//                    text: fishSampling.specimensModel.get(styleData.row)["specimenID"]
//                    text: (styleData.value) &
//                            (fishSampling.specimensModel.get(styleData.row)["speciesSamplingPlanID"] === null) ?
//                            styleData.value : ""
//                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // ageID
            TableViewColumn {
                role: "finclipID"
                title: "Finclip"
                width: 80
                delegate: Text {
                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // finclipID
            TableViewColumn {
                role: "special"
                title: "Special"
                width: 200
                delegate: Text {
                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // special
            TableViewColumn {
                role: "disposition"
                title: "Dis"
                width: 80
                delegate: Text {
                    text: getDispositionLabel(styleData.row, styleData.value);
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // disposition

            selection.onSelectionChanged: {
                if (currentRow != -1) {
                    if (tvSpecimens.selection.contains(currentRow)) {
                        var currentAdh = fishSampling.specimensModel.get(currentRow).adh;
                        if ((currentAdh !== undefined) && (currentAdh.length === 3)) {
                            stateMachine.angler = currentAdh.charAt(0);
                            stateMachine.drop = currentAdh.charAt(1);
                            stateMachine.hook = currentAdh.charAt(2);
                        } else {
                            stateMachine.angler = null;
                            stateMachine.drop = null;
                            stateMachine.hook = null;
                        }
                    } else {
                        stateMachine.angler = null;
                        stateMachine.drop = null;
                        stateMachine.hook = null;
                    }

                    // If the selection change is coming from the FishSamplingScreen, proceed,
                    //  otherwise skip this as it is coming from the FishSamplingEntryDialog.qml
                    //  and so we do not want to nullify the currentEntryTab if that is the case
                    if (!externalUpdate) {
                        stateMachine.currentEntryTab = null;
                        console.info('currentRow = ' + currentRow + ', state machine adh = ' +
                            stateMachine.angler + stateMachine.drop + stateMachine.hook +
                            ', stateMachine.currentEntryTab = ' + stateMachine.currentEntryTab);
                    }
                    externalUpdate = false;
                }
            }

            onDoubleClicked: {
                editSpecimen();
            }
        } // tvSpecimens
    }
//    OkayDialog { id: dlgFishSamplingEntry }
    FishSamplingEntryDialog { id: dlgFishSamplingEntry; }
    OkayCancelDialog {
        id: dlgOkayCancel
        onAccepted: {
            switch (accepted_action) {
                case "delete specimen":
                    var id = fishSampling.specimensModel.get(tvSpecimens.currentRow).specimenID;
                    if (id !== undefined) {
                        fishSampling.deleteSpecimenRecord(id);
                        tvSpecimens.selection.clear();
                    }
                    break;
            }
        }
    }
    OkayDialog { id: dlgOkay }
    DrawingNotesDialog { id: dlgDrawingNotes }
    RecordedByDialog {
        id: dlgRecordedBy;
        onRecorderChanged: updateRecorder(id, name);
        function updateRecorder(id, name) {
            fishSampling.updateRecorder(id, name);
            stateMachine.recorder = name;
//            btnRecordedBy.text = "Recorded By\n" + name.substring(0,11);
        }
    }
}