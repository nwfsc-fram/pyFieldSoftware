import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "special"
    property int buttonBaseSize: 80
    property alias tvSpecial: tvSpecial;
    property alias btnAssignLabel: btnAssignLabel;

    signal labelSet(string action, string value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();

    Connections {
        target:  fishSampling
        onSpecimenObservationUpdated:  updateSpecialModel(speciesSamplingPlanId, modelType, id, tagNumber);
    } // fishSampling.onSpecimenObservationUpdated
    function updateSpecialModel(speciesSamplingPlanId, modelType, id, tagNumber) {
        console.info('sspi=' + speciesSamplingPlanId + ', modelType=' + modelType + ', id=' +
                        id + ', tagNumber=' + tagNumber);
        var idx = fishSampling.specialsModel.get_item_index("speciesSamplingPlanID", speciesSamplingPlanId)
        if (idx !== -1) {
            var item = fishSampling.specialsModel.get(idx);
            console.info('model item=' + JSON.stringify(item));
            var tagType = item.tagType;
//            tagType = tagType.replace(" ", "").toLowerCase();
            tagType = tagType.replace(/ /gi, "").toLowerCase();
            modelType = modelType.toLowerCase();
            console.info('modelType=' + modelType + ', tagType=' + tagType);
            if ((tagType === modelType) && (item.speciesSamplingPlanID === speciesSamplingPlanId)) {
                tvSpecial.model.setProperty(idx, "id", id);
                tvSpecial.model.setProperty(idx, "tagNumber", tagNumber);

                item = fishSampling.specialsModel.get(idx);
                console.info('new item info=' + JSON.stringify(item));
            }
        }
    }
    function clearState() {
        tvSpecial.selection.clear();
        tvSpecial.currentRow = -1;
    }
    function printLabel() {
        if (tvSpecial.currentRow !== -1) {
            var item = tvSpecial.model.get(tvSpecial.currentRow);
            var tagNumber = item["tagNumber"];
            var observation = item["tagType"];
            var project = item["project"];
//            var speciesObservations = parent.parent.parent.parent.retrieveSpeciesObservations();
            var speciesObservations = parent.retrieveSpeciesObservations();
            console.info('speciesObservations=' + JSON.stringify(speciesObservations));
            labelPrinter.printHookAndLineTagNumber(tagNumber, observation,
                speciesObservations, project);
        }
    }
    function assignLabel() {
        if (tvSpecial.currentRow !== -1) {
            var item = tvSpecial.model.get(tvSpecial.currentRow);
            console.info('item = ' + JSON.stringify(item));
            var specimenID = parent.retrieveSpecimenID();
            console.info('parent specimenID=' + specimenID);
            var project = item["project"]
            var sspi = item["speciesSamplingPlanID"];
            var observationType = item["tagType"];
            var observationSubType = item["tagSubType"]
            var species = parent.retrieveLabelElements();
            if (species === null) {
                dlgOkay.message = "Species is required for the tag number.\n";
                dlgOkay.action = "Please identify the species first.";
                dlgOkay.open();
                return;
            }
            var finclipID = parent.retrieveFinclipID();
            console.info('finclipID=' + JSON.stringify(finclipID));

            if ((finclipID === null) || (finclipID.length < 5)) {
                dlgOkay.message = "A 5 character Finclip ID is required for the tag number.\n";
                dlgOkay.action = "Please record the Finclip ID first.";
                dlgOkay.open();
                return;
            }

            var speciesIndicator = "A";
            switch (species) {
                case "Bocaccio":
                    speciesIndicator = "B";
                    break;
                case "Vermilion Rockfish":
                    speciesIndicator = "V";
                    break;
//                case "Greenspotted Rockfish":
//                    speciesIndicator = "G";
//                    break;
            }
            var tagNumber = fishSampling.assignHookAndLineTagNumber(specimenID, project, sspi, observationType,
                                                                    speciesIndicator, finclipID, observationSubType);
            tvSpecial.model.setProperty(tvSpecial.currentRow, "tagNumber", tagNumber);
            var row = tvSpecial.currentRow;
            tvSpecial.currentRow = -1;
            tvSpecial.currentRow = row;

            var specialValue = fishSampling.specialsModel.getSpecialTabLabel();
            updateLabel("special", specialValue, null, false, null);
            printLabel();
        }
    }
    RowLayout {
        spacing: 20
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        BackdeckTableView {
            id: tvSpecial
            Layout.preferredWidth: 800
            Layout.preferredHeight: 400
            selectionMode: SelectionMode.SingleSelection
            headerVisible: true
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

            model: fishSampling.specialsModel

            TableViewColumn {
                role: "project"
                title: "Project"
                width: 300
            } // pi
            TableViewColumn {
                role: "tagType"
                title: "Tag Type"
                width: 240
            } // tagType
            TableViewColumn {
                role: "tagNumber"
                title: "Tag Number"
                width: 240
                delegate: Text {
                    text: styleData.value ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // tagNumber

            style: TableViewStyle {
                itemDelegate: Item {
                    height: textItem.implicitHeight * 1.2
                    Text {
                        id: textItem
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: styleData.textAlignment
                        anchors.leftMargin: 12
                        text: styleData.value ? styleData.value : ""
                        font.pixelSize: 20
                    }
                    Rectangle {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 1
                        anchors.topMargin: 1
                        height: 60
                    }
                }
                rowDelegate: Rectangle {
                    height: 60
                    color: styleData.selected ? "skyblue" : (styleData.alternate? "#eee" : "#fff")
                }
                headerDelegate: Rectangle {
                    height: textItem.implicitHeight * 1.2
                    width: textItem.implicitWidth
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "white" }
                        GradientStop { position: 1.0; color: "lightgray" }
                    }
                    border.color: "gray"
                    border.width: 1
                    Text {
                        id: textItem
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: styleData.textAlignment
                        anchors.leftMargin: 12
                        text: styleData.value
                        elide: Text.ElideRight
                        color: textColor
                        renderType: Text.NativeRendering
                        font.pixelSize: 20
                    }
                    Rectangle {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 1
                        anchors.topMargin: 1
                        width: 1
        //                color: "#ccc"
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "white" }
                            GradientStop { position: 1.0; color: "#eee" }
        //                    GradientStop { position: 1.0; color: "lightgray" }
                        }
                    }
                }
            }
        } // tvSpecial
        ColumnLayout {
            spacing: 20
            BackdeckButton {
                id: btnAssignLabel
                text: qsTr("Assign & Print\nLabel")
                Layout.preferredHeight: buttonBaseSize
                Layout.preferredWidth: buttonBaseSize * 2
                state: tvSpecial.currentRow !== -1 ? "enabled" : "disabled"
                onClicked: {
                    if (tvSpecial.currentRow !== -1) {
                        var item = tvSpecial.model.get(tvSpecial.currentRow);
                        if ((item.tagNumber === undefined) || (item.tagNumber === "")) {
                            assignLabel();
//                            printLabel();
                        }
                    }
                }
            } // btnAssignLabel
            BackdeckButton {
                id: btnDeleteLabel
                text: qsTr("Delete\nLabel")
                Layout.preferredHeight: buttonBaseSize
                Layout.preferredWidth: buttonBaseSize * 2
                state: ((tvSpecial.currentRow !== -1) &&
                        (tvSpecial.model.get(tvSpecial.currentRow).tagNumber !== undefined) &&
                        (tvSpecial.model.get(tvSpecial.currentRow).tagNumber !== ""))
                             ? "enabled" : "disabled"
                onClicked: {
                    if (tvSpecial.currentRow !== -1) {
                        var item = tvSpecial.model.get(tvSpecial.currentRow);
                        if ((item.tagNumber !== undefined) && (item.tagNumber !== "")) {
                            dlgOkayCancel.message = "You are about to delete this specimen"
                            dlgOkayCancel.action = "Click Okay to delete it or Cancel to keep it"
                            dlgOkayCancel.accepted_action = "delete specimen"
                            dlgOkayCancel.open();
                        }
                    }
                }
            } // btnDeleteLabel
            BackdeckButton {
                id: btnSerialPortManager
                text: qsTr("Serial Port\nManager");
                Layout.preferredHeight: buttonBaseSize
                Layout.preferredWidth: buttonBaseSize * 2
                onClicked: {
                    dlgSPM.open()
                }
            } // btnSerialPortManager
        } // printer buttons
    }
    SerialPortManagerDialog { id: dlgSPM }
    OkayDialog { id: dlgOkay }
    OkayCancelDialog {
        id: dlgOkayCancel
        onAccepted: {
            switch (accepted_action) {
                case "delete specimen":
                    if (tvSpecial.currentRow !== -1) {

                        var item = tvSpecial.model.get(tvSpecial.currentRow);
                        console.info('deleting item=' + JSON.stringify(item));
                        fishSampling.deleteSpecimenObservation(item['id'], item['tagType'], null, true);
                        tvSpecial.model.setProperty(tvSpecial.currentRow, "tagNumber", null);
                        tvSpecial.model.setProperty(tvSpecial.currentRow, "id", null);

                        // Resets the enabled status of the row
                        var row = tvSpecial.currentRow;
                        tvSpecial.currentRow = -1;
                        tvSpecial.currentRow = row;

                        var specialValue = fishSampling.specialsModel.getSpecialTabLabel();
                        updateLabel("special", specialValue, null, false, null);
                    }
                    break;
            }
        }
    }
}