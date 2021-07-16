import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1
//import QtQuick.Controls.Styles 1.2
//import QtQuick.Controls.Private 1.0

Item {

    id: itmDropTab

    // TODO Todd Hay - if reopening a site, need to ensure that rtA, rtB, and rtC are enabled
    property string dropNumber: "1"
    property variant dropOpId: drops.getDropIdFromNumber(dropNumber)  // dropNumber var above changes with each tab
    property int buttonWidth: 140
    property string sinkerWeight: "Sinker\nlb";

    property alias anglerA: anglerA
    property alias anglerB: anglerB
    property alias anglerC: anglerC
    property string recorder: ""

    implicitWidth: parent.width;

    signal newDropAdded(variant dropJson);

    Connections {
        target: anglerA
        onDropStarted: startAnglerDrop(anglerLetter, startSeconds, timeStr);
    } // anglerA.onDropStarted
    Connections {
        target: anglerB
        onDropStarted: startAnglerDrop(anglerLetter, startSeconds, timeStr);
    } // anglerB.onDropStarted
    Connections {
        target: anglerC
        onDropStarted: startAnglerDrop(anglerLetter, startSeconds, timeStr);
    } // anglerC.onDropStarted
    function startAnglerDrop(anglerLetter, startSeconds, timeStr) {

        // Reset the retrievalSoundPlayed which determines if a sound is played at 04:45 or not
        retrievalSoundPlayed = false;

        // Insert new OPERATIONS table records - One Drop + Three Anglers records
        var op_ids = drops.insertOperations(dropNumber);
        if (op_ids === undefined) {
            console.info('op_ids=' + JSON.stringify(op_ids));
            return;
        }

        var operationId = null;
        var luType = "Angler Time";
        var luValue = "Start";
        var valueType = "alpha";
        var value = timeStr;

        if ((anglerA.btnStart.text === "Start\n") ||
            ((anglerA.btnStart.text !== "Start\n") & (anglerLetter === "A"))){
            anglerA.startSeconds = startSeconds;
            anglerA.startDrop(timeStr);

            // Insert new OPERATION_ATTRIBUTES records
            operationId = op_ids["Angler A"];
            anglerA.operationId = operationId  // #251: set op id for angler QML item, this wont change
            drops.upsertOperationAttribute(operationId, luType, luValue, valueType, value, "Angler A");
            console.info('insert Angler A');
        }
        if ((anglerB.btnStart.text === "Start\n") ||
            ((anglerB.btnStart.text !== "Start\n") & (anglerLetter === "B"))) {
            anglerB.startSeconds = startSeconds;
            anglerB.startDrop(timeStr);

            // Insert new OPERATION_ATTRIBUTES records
            operationId = op_ids["Angler B"];
            anglerB.operationId = operationId  // #251: set op id for angler QML item, this wont change
            drops.upsertOperationAttribute(operationId, luType, luValue, valueType, value, "Angler B");
            console.info('insert Angler B');

        }
        if ((anglerC.btnStart.text === "Start\n") ||
            ((anglerC.btnStart.text !== "Start\n") & (anglerLetter === "C"))) {
            anglerC.startSeconds = startSeconds;
            anglerC.startDrop(timeStr);

            // Insert new OPERATION_ATTRIBUTES records
            operationId = op_ids["Angler C"];
            anglerC.operationId = operationId  // #251: set op id for angler QML item, this wont change
            drops.upsertOperationAttribute(operationId, luType, luValue, valueType, value, "Angler C");
            console.info('insert Angler C');

        }

        // Emit signal for DropScreen.qml to pick up to add the new dropJson to the siteResults JSON
        var dropKey = "Drop " + stateMachine.drop;
        var dropJson = {};
        dropJson[dropKey] =
            {"id": op_ids[dropKey],
             "Anglers": {
                    "Angler A": {"id": op_ids["Angler A"]},
                    "Angler B": {"id": op_ids["Angler B"]},
                    "Angler C": {"id": op_ids["Angler C"]}
                }
            };
        newDropAdded(dropJson);

    }

    Connections {
        target: dlgPersonnel
        onPersonnelSet: updatePersonnel(anglerA, anglerB, anglerC, recorder);
    } // dlgPersonnel.onPersonnelSet
    function updatePersonnel(personA, personB, personC, personRecorder) {

        // Updating Personnel
        anglerA.anglerName = personA;
        anglerB.anglerName = personB;
        anglerC.anglerName = personC;
        recorder = personRecorder;

        if (dropNumber == "1") {
            // Update all five drops to be these same 4 people, i.e. make them sticky across all drops at the site

        } else {
            // Only update the current drop if we're not on dropNumber == "1"

        }

        // TODO - Todd Hay - Update database with new angler name information
        if (personA !== "") {
            drops.upsertOperationAttribute(stateMachine.anglerAOpId, "Angler Attribute", "Angler Name", "alpha", personA, "Angler A");
            anglerA.operationId = stateMachine.anglerAOpId  // #251: setting static op id for angler upon row creation
            console.debug("Updating operationIDs, angler A: " + stateMachine.anglerAOpId)
        }
        if (personB !== "") {
            drops.upsertOperationAttribute(stateMachine.anglerBOpId, "Angler Attribute", "Angler Name", "alpha", personB, "Angler B");
            anglerB.operationId = stateMachine.anglerBOpId  // #251: setting static op id for angler upon row creation
            console.debug("Updating operationIDs, angler B: " + stateMachine.anglerBOpId)
        }
        if (personC !== "") {
            drops.upsertOperationAttribute(stateMachine.anglerCOpId, "Angler Attribute", "Angler Name", "alpha", personC, "Angler C");
            anglerC.operationId = stateMachine.anglerCOpId  // #251: setting static op id for angler upon row creation
            console.debug("Updating operationIDs, angler C: " + stateMachine.anglerCOpId)
        }
        if (personRecorder !== "")
            drops.upsertOperationAttribute(stateMachine.dropOpId, "Drop Attribute", "Recorder Name", "alpha", personRecorder, "Drop " + dropNumber);
    }

    Connections {
        target: anglerA
        onOpenPersonnelDialog: personnelDialogOpen(anglerLetter);
    } // anglerA.onOpenPersonnelDialog
    Connections {
        target: anglerB
        onOpenPersonnelDialog: personnelDialogOpen(anglerLetter);
    } // anglerB.onOpenPersonnelDialog
    Connections {
        target: anglerC
        onOpenPersonnelDialog: personnelDialogOpen(anglerLetter);
    } // anglerC.onOpenPersonnelDialog
    function personnelDialogOpen(anglerLetter) {
        dlgPersonnel.anglerA.tfPersonnel.deselect();
        dlgPersonnel.anglerB.tfPersonnel.deselect();
        dlgPersonnel.anglerC.tfPersonnel.deselect();
        dlgPersonnel.recorder.tfPersonnel.deselect();

        dlgPersonnel.anglerA.tfPersonnel.text = anglerA.anglerName;
        dlgPersonnel.anglerB.tfPersonnel.text = anglerB.anglerName;
        dlgPersonnel.anglerC.tfPersonnel.text = anglerC.anglerName;
        dlgPersonnel.recorder.tfPersonnel.text = recorder;

        var currentAngler;
        switch (anglerLetter) {
            case "A":
                currentAngler = dlgPersonnel.anglerA;
                break;
            case "B":
                currentAngler = dlgPersonnel.anglerB;
                break;
            case "C":
                currentAngler = dlgPersonnel.anglerC;
                break;
        }
        dlgPersonnel.currentPerson = currentAngler;
        currentAngler.tfPersonnel.selectAll();
        currentAngler.tfPersonnel.forceActiveFocus();

        dlgPersonnel.open();
    }

    signal sinkerWeightsUpdated(double result);

    Connections {
        target: dlgSinkerWeight
        onResultCaptured: updateSinkerWeight(result);
    } // dlgSinkerWeight.resultCaptured
    function updateSinkerWeight(result) {
        sinkerWeight = qsTr("Sinker\n" + result + " lb");
        drops.upsertOperationAttribute(stateMachine.dropOpId, "Drop Attribute", "Sinker Weight", "numeric",
                                        parseInt(result), "Drop " + dropNumber);
        if (dropNumber == "1") {
            sinkerWeightsUpdated(result)
        }
    }

    property bool retrievalSoundPlayed: false;
    function playRetrievalSound() {
        if (!retrievalSoundPlayed) {
            retrievalSoundPlayed = true;
            drops.playSound("hlHookMatrix15secs");
        }
    }

    BackdeckButton {
        id: btnSinker
        text: sinkerWeight
        width: buttonWidth
        height: 80
        anchors.top: parent.top
        anchors.topMargin: 10
        anchors.right: parent.right
        anchors.rightMargin: 10
        onClicked: {
            dlgSinkerWeight.setWeight(parseInt(text.split("\n")[1].replace(" lb", "")));
            dlgSinkerWeight.open();
        }
    } // btnSinker
    ColumnLayout {
        anchors.left: parent.left
        anchors.leftMargin: 20
        anchors.top: parent.top
        anchors.topMargin: 20
        spacing: 40
        DropAngler {
            id: anglerA
            anglerLetter: "A"
            anglerPosition: "Bow"
            anglerName: ""
            onRetrievalTimeReached: { playRetrievalSound(); }
        } // anglerA
        DropAngler {
            id: anglerB
            anglerLetter: "B"
            anglerPosition: "Mid"
            anglerName: ""
            onRetrievalTimeReached: { playRetrievalSound(); }
        } // anglerB
        DropAngler {
            id: anglerC
            anglerLetter: "C"
            anglerPosition: "Stern"
            anglerName: ""
            onRetrievalTimeReached: { playRetrievalSound(); }
        } // anglerC
    }
    SinkerWeightDialog { id: dlgSinkerWeight }
    PersonnelDialog { id: dlgPersonnel }
}