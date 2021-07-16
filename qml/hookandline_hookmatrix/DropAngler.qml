import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4

Item {

    signal openPersonnelDialog(variant anglerLetter);
    signal retrievalTimeReached();

    property string anglerPosition: "Bow";
    property string anglerLetter: "A";
    property string anglerName: "Bob Jones";
    property double startSeconds;
    property bool isRunning: false;

    property alias btnAnglerName: btnAnglerName;
    property alias lblElapsedTime: lblElapsedTime;

    property alias btnStart: btnStart;
    property alias btnBeginFishing: btnBeginFishing;
    property alias btnFirstBite: btnFirstBite;
    property alias btnRetrieval: btnRetrieval;
    property alias btnAtSurface: btnAtSurface;
    property alias rtHooks: rtHooks;

    property variant operationId;  // #251: angler op id set to null on init, populated as DB records are created
    property string luType: "Angler Time"
    property string luValue: ""
    property string valueType: "alpha"
    property string value: ""
    property variant lastButtonClicked: null
    property variant previousButtonsState: {
            "Start": btnStart.enabled, "Begin Fishing": btnBeginFishing.enabled,
            "First Bite": btnFirstBite.enabled, "Retrieval": btnRetrieval.enabled,
            "At Surface": btnAtSurface.enabled
        }

    implicitHeight: clDropAngler.implicitHeight

    signal dropStarted(string anglerLetter, double startSeconds, string timeStr);

    Connections {
        target: stateMachine
        onDropTimeStateChanged: changeButtonsStatus();
    } // stateMachine.onDropTimeStateChanged
    function changeButtonsStatus() {

//        console.info("dropTimeState=" + stateMachine.dropTimeState + ", previousButtonsState: " +
//                        JSON.stringify(previousButtonsState));

        switch (stateMachine.dropTimeState) {
            case "enter":
                // Set the button to it's previous state
                for (var key in previousButtonsState) {
                    switch (key) {
                        case "Start":
                            btnStart.enabled = previousButtonsState[key];
                            break;
                        case "Begin Fishing":
                            btnBeginFishing.enabled = previousButtonsState[key];
                            break;
                        case "First Bite":
                            btnFirstBite.enabled = previousButtonsState[key];
                            break;
                        case "Retrieval":
                            btnRetrieval.enabled = previousButtonsState[key];
                            break;
                        case "At Surface":
                            btnAtSurface.enabled = previousButtonsState[key];
                            break;
                    }
                }
                break;
            case "edit":
                // Enable Editing on buttons that have a time
                btnStart.enabled = (btnStart.text == "Start\n") ? false : true;
                btnBeginFishing.enabled = (btnBeginFishing.text == "Begin Fishing\n") ? false :true;
                btnFirstBite.enabled = (btnFirstBite.text == "First Bite\n") ? false : true;
                btnRetrieval.enabled = (btnRetrieval.text == "Retrieval\n") ? false : true;
                btnAtSurface.enabled = (btnAtSurface.text == "At Surface\n") ? false : true;
                break;
            case "delete":
                // Enable All Time Buttons
                btnStart.enabled = (btnStart.text == "Start\n") ? false : true;
                btnBeginFishing.enabled = (btnBeginFishing.text == "Begin Fishing\n") ? false :true;
                btnFirstBite.enabled = (btnFirstBite.text == "First Bite\n") ? false : true;
                btnRetrieval.enabled = (btnRetrieval.text == "Retrieval\n") ? false : true;
                btnAtSurface.enabled = (btnAtSurface.text == "At Surface\n") ? false : true;
                break;
            case "move":
                break;
            case "swap":
                break;
        }
    }

    Timer { id: timer }
    function startTimer() {
//        var soundElapsedTimeStr = "04:45";
        var soundElapsedTimeStr = "";
        var beginFishingTime;
        timer.interval = 100;
        timer.repeat = true;
        var newTime;
        var i = 1;
        timer.triggered.connect(function () {
            if (!isRunning) {
                timer.stop()
            }
            if (btnBeginFishing.text !== "Begin Fishing\n" && soundElapsedTimeStr === "") {
                beginFishingTime = btnBeginFishing.text.replace("Begin Fishing\n", "");
                soundElapsedTimeStr = drops.getSoundPlaybackTime(beginFishingTime);
                console.info('time to compare: ' + soundElapsedTimeStr);
            }

            if (i == 10) {
                newTime = (new Date()).getTime();
                lblElapsedTime.text = formatTime((newTime - startSeconds)/1000);
                i = 1;

                if (lblElapsedTime.text === soundElapsedTimeStr) {
                    retrievalTimeReached();
                }

            } else
                i++;
        })
        timer.start();
    }
    function calculateFiveMinDuration(beginFishingTime) {
        var fiveMinDuration;
        
    }

    function startDrop(timeStr) {
        btnStart.text = "Start\n" + timeStr;
        btnBeginFishing.enabled = true;
        btnFirstBite.enabled = true;
        btnRetrieval.enabled = true;
        isRunning = true;
        startTimer();
    }
    function getOperationId() {
        // #251: No longer used in favor of assigning opId directly to DropAngler object
        switch (anglerLetter) {
            case "A":
                operationId = stateMachine.anglerAOpId;
                break;
            case "B":
                operationId = stateMachine.anglerBOpId;
                break;
            case "C":
                operationId = stateMachine.anglerCOpId;
                break;
        }
    }
    function timeButtonClicked(btn) {
        lastButtonClicked = btn;

        console.info('dropTimeState: ' + stateMachine.dropTimeState + ", btn: " + btn.text);
        var btnStr;
        switch (stateMachine.dropTimeState) {
            case "enter":
                switch (btn) {
                    case btnStart:
                        lblElapsedTime.text = qsTr("00:00");
                        var d = new Date();
                        startSeconds = d.getTime();
                        var timeStr = padZeros(d.getHours()) + ":" + padZeros(d.getMinutes()) + ":" + padZeros(d.getSeconds());
                        dropStarted(anglerLetter, startSeconds, timeStr);
                        updateButtonStatus("Start");
                        break;
                    case btnBeginFishing:
                        var newTime = (new Date()).getTime();
                        var elapsedTime = formatTime((newTime - startSeconds)/1000);
                        btnBeginFishing.text = "Begin Fishing\n" + elapsedTime;
//                        btnStart.enabled = false;
                        updateButtonStatus("Begin Fishing");
                        drops.upsertOperationAttribute(operationId, luType, "Begin Fishing", valueType, elapsedTime,
                                                        "Angler " + anglerLetter);
                        break;
                    case btnFirstBite:
                        var newTime = (new Date()).getTime();
                        var elapsedTime = formatTime((newTime - startSeconds)/1000);
                        btnFirstBite.text = "First Bite\n" + elapsedTime;
                        if (btnBeginFishing.text == "Begin Fishing\n") {
                            btnBeginFishing.text = "Begin Fishing\n" + elapsedTime;
                            drops.upsertOperationAttribute(operationId, luType, "Begin Fishing", valueType, elapsedTime,
                                                        "Angler " + anglerLetter);
                        }
                        updateButtonStatus("First Bite");
                        drops.upsertOperationAttribute(operationId, luType, "First Bite", valueType, elapsedTime,
                                                        "Angler " + anglerLetter);
                        break;
                    case btnRetrieval:
                        var newTime = (new Date()).getTime();
                        var elapsedTime = formatTime((newTime - startSeconds)/1000);
                        btnRetrieval.text = "Retrieval\n" + elapsedTime;
                        updateButtonStatus("Retrieval");
                        drops.upsertOperationAttribute(operationId, luType, "Retrieval", valueType, elapsedTime,
                                                        "Angler " + anglerLetter);
                        break;
                    case btnAtSurface:
                        var newTime = (new Date()).getTime();
                        var elapsedTime = formatTime((newTime - startSeconds)/1000);
                        btnAtSurface.text = "At Surface\n" + elapsedTime;
                        lblElapsedTime.text = elapsedTime;
                        rtHooks.enabled = true;
                        isRunning = false;
                        updateButtonStatus("At Surface");
                        drops.upsertOperationAttribute(operationId, luType, "At Surface", valueType, elapsedTime,
                                                        "Angler " + anglerLetter);
                        break;
                }
                break;
            case "edit":
                var timeStrArr = btn.text.split('\n')[1].split(":");
                if (timeStrArr.length === 2) {
                    dlgEditTime.currentMinutes = timeStrArr[0];
                    dlgEditTime.currentSeconds = timeStrArr[1];
                    dlgEditTime.numPad.tfMinutes.text = dlgEditTime.currentMinutes;
                    dlgEditTime.numPad.tfSeconds.text = dlgEditTime.currentSeconds;
                }
                dlgEditTime.editedButton = btn;
                dlgEditTime.numPad.tfMinutes.selectAll();
                dlgEditTime.numPad.tfMinutes.forceActiveFocus();
                dlgEditTime.open();
                break;
            case "delete":
                btnStr = btn.text.split("\n")[0];
                dlgOkayCancel.message = "You are about to delete the " + btnStr + " time"
                dlgOkayCancel.action = "Are you sure that you want to do this?"
                dlgOkayCancel.actionType = "delete"
                dlgOkayCancel.btn = btn;
                dlgOkayCancel.open();
                break;
            case "move":
                break;
            case "swap":
                break;
        }
//        stateMachine.dropTimeState = "enter";
//        lastButtonClicked = btn.text.split("\n")[0];
    }
    function getButtonStatus(btnStr) {
        switch (btnStr) {
                case null:
                    btnStart.enabled = true;
                    break;
                case "Start":
                    btnStart.enabled = true;
                    btnBeginFishing.enabled = true;
                    btnFirstBite.enabled = true;
                    btnRetrieval.enabled = true;
                    break;
                case "Begin Fishing":
                    btnBeginFishing.enabled = true;
                    btnFirstBite.enabled = true;
                    btnRetrieval.enabled = true;
                    break;
                case "First Bite":
                    btnFirstBite.enabled = true;
                    btnRetrieval.enabled = true;
                    if (btnRetrieval.text !== "Retrieval\n") {
                        btnAtSurface.enabled = true;
                    }
                    break;
                case "Retrieval":
                    btnFirstBite.enabled = true;
                    btnRetrieval.enabled = true;
                    btnAtSurface.enabled = true;
                    break;
                case "At Surface":
                    btnAtSurface.enabled = true;
                    break;
            }
    }
    function updateButtonStatus(btnStr) {

        console.info('btnStr: ' + btnStr);

        // Disable All Time Buttons
        btnStart.enabled = false;
        btnBeginFishing.enabled = false;
        btnFirstBite.enabled = false;
        btnRetrieval.enabled = false;
        btnAtSurface.enabled = false;

        // Enabled Based on the Button Provided
        switch (btnStr) {
            case null:
                btnStart.enabled = true;
                break;
            case "Start":
                btnStart.enabled = true;
                btnBeginFishing.enabled = true;
                btnFirstBite.enabled = true;
                btnRetrieval.enabled = true;
                break;
            case "Begin Fishing":
                btnBeginFishing.enabled = true;
                btnFirstBite.enabled = true;
                btnRetrieval.enabled = true;
                break;
            case "First Bite":
                btnFirstBite.enabled = true;
                btnRetrieval.enabled = true;
                if (btnRetrieval.text !== "Retrieval\n") {
                    btnAtSurface.enabled = true;
                }
                break;
            case "Retrieval":
                btnFirstBite.enabled = true;
                btnRetrieval.enabled = true;
                btnAtSurface.enabled = true;
                break;
            case "At Surface":
                btnAtSurface.enabled = true;
                break;
        }

        // Save the current buttons state as the previous state of the buttons
        previousButtonsState = {
            "Start": btnStart.enabled, "Begin Fishing": btnBeginFishing.enabled,
            "First Bite": btnFirstBite.enabled, "Retrieval": btnRetrieval.enabled,
            "At Surface": btnAtSurface.enabled
        }

    }

    ColumnLayout {
        id: clDropAngler
        spacing: 10
        RowLayout {
            anchors.left: parent.left
            anchors.leftMargin: 20
            spacing: 80
            Label {
                id: lblAnglerLetter
                text: anglerPosition + " - " + anglerLetter
                font.pixelSize: 40
                Layout.preferredWidth: 120
            } // lblAnglerLetter
            BackdeckButton {
                id: btnAnglerName
                Layout.preferredHeight: 60
                Layout.preferredWidth: 220
                text: anglerName
                onClicked: {
                    openPersonnelDialog(anglerLetter);
                }
            } // btnAnglerName
            Label { Layout.preferredWidth: 40 }
            Label {
                id: lblElapsedTime
                text: "00:00"
                font.pixelSize: 40
            } // lblElapsedTime
        } // Labels + Personnel + Elapsed Time
        RowLayout {
            spacing: 15
            BackdeckButton {
                id: btnStart
                text: qsTr("Start\n")
                Layout.preferredWidth: buttonWidth
                Layout.preferredHeight: 80
                onClicked: {
                    timeButtonClicked(btnStart);
                }
            } // btnStart
            BackdeckButton {
                id: btnBeginFishing
                text: qsTr("Begin Fishing\n")
                Layout.preferredWidth: buttonWidth
                Layout.preferredHeight: 80
                enabled: false
                onClicked: {
                    timeButtonClicked(btnBeginFishing);
                }
            } // btnBeginFishing
            BackdeckButton {
                id: btnFirstBite
                text: qsTr("First Bite\n")
                Layout.preferredWidth: buttonWidth
                Layout.preferredHeight: 80
                enabled: false
                onClicked: {
                    timeButtonClicked(btnFirstBite);
                }
            } // btnFirstBite
            BackdeckButton {
                id: btnRetrieval
                text: qsTr("Retrieval\n")
                Layout.preferredWidth: buttonWidth
                Layout.preferredHeight: 80
                enabled: false
                onClicked: {
                    timeButtonClicked(btnRetrieval);
                }
            } // btnRetrieval
            BackdeckButton {
                id: btnAtSurface
                text: qsTr("At Surface\n")
                Layout.preferredWidth: buttonWidth
                Layout.preferredHeight: 80
                enabled: false
                onClicked: {
                    timeButtonClicked(btnAtSurface);
                }
            } // btnAtSurface
            Rectangle {
                id: rtGearPerformance
                antialiasing: true
                height: 40
                radius: 4
                implicitWidth:  txtGearPerformance.implicitWidth + imgGearPerformance.implicitWidth
                enabled: operationId ? true : false  // # 247: only allow nav to GP after angler id created
                color: "transparent"

                Text {
                    id: txtGearPerformance
                    text: operationId ? drops.getAnglerGearPerfsLabel(operationId) : "Gear\nPerf."  // #241: query perfs by angler ID
                    font.pixelSize: 24
                    color: rtGearPerformance.enabled ? 'black' : 'gray'  // #246: gray if disabled
                    font.italic: !rtGearPerformance.enabled  // #246: italic if disabled
                    anchors.verticalCenter: parent.verticalCenter
                    Connections { // #241: receive signal from GearPerformance whenever record is added/deleted
                        target: gearPerformance
                        onGearPerformanceChanged: {
                            if(angler_op_id == operationId) {  // only query if DB Ids match
                                txtGearPerformance.text = drops.getAnglerGearPerfsLabel(operationId)
                            }
                        }
                    }
                }
                Image {
                    id: imgGearPerformance
                    opacity: rtGearPerformance.enabled ? 1.0 : 0.25  // #246: set image opaque if disabled
                    anchors.left: txtGearPerformance.right
                    anchors.verticalCenter: parent.verticalCenter
                    source: Qt.resolvedUrl("/resources/images/navigation_next_item_dark.png")
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        stateMachine.angler = anglerLetter
                        smHookMatrix.to_gear_performance_state();
                    }
                }

            } // rtGearPerformance
            Rectangle {
                id: rtHooks
                antialiasing: true
                height: 40
                radius: 4
                implicitWidth:  txtHooks.implicitWidth + imgHooks.implicitWidth
                color: "transparent"
                enabled: false
                Text {
                    id: txtHooks
                    text: drops.getAnglerHooksLabel(operationId, rtHooks.enabled)
                    font.pixelSize: 24
                    anchors.verticalCenter: parent.verticalCenter
                    Connections {
                        target: hooks
                        onHooksChanged: {
                            if (angler_op_id == operationId) {
                                txtHooks.text = drops.getAnglerHooksLabel(operationId, rtHooks.enabled)
                            }
                        }
                    }
                    Connections {
                        target: gearPerformance
                        onHooksUndeployed: {
                            if (angler_op_id == operationId) {
                                txtHooks.text = drops.getAnglerHooksLabel(operationId, rtHooks.enabled)
                            }
                        }
                    }
                }
                Image {
                    id: imgHooks
                    anchors.left: txtHooks.right
                    opacity: rtHooks.enabled ? 1.0 : 0.25  // #246: set image opaque if disabled
                    anchors.verticalCenter: parent.verticalCenter
                    source: Qt.resolvedUrl("/resources/images/navigation_next_item_dark.png")
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        stateMachine.angler = anglerLetter;
                        stateMachine.anglerName = anglerName;
                        smHookMatrix.to_hooks_state();
                    }
                }
            } // rtHooks
            Connections {
            	target: gearPerformance
            	onAnglerTimeUndeployed: {
            	    // #144: receive signal from gp when undeployed is selected, set times to undeployed str
            		if (angler_op_id == operationId) {
            			switch(time_type) {
            				case "Start":
            					btnStart.text = "Start\n" + undeployed_str;
            					break;
            				case "Begin Fishing":
            					btnBeginFishing.text = "Begin Fishing\n" + undeployed_str;
            					break;
            				case "First Bite":
            					btnFirstBite.text = "First Bite\n" + undeployed_str;
            					break;
            				case "Retrieval":
            					btnRetrieval.text = "Retrieval\n" + undeployed_str;
            					break;
            				case "At Surface":
            				    // mimic ending of time recording for normal deployed fishing
            					btnAtSurface.text = "At Surface\n" + undeployed_str;
            					lblElapsedTime.text = btnAtSurface.text.replace("At Surface\n", "");
            					rtHooks.enabled = true;
            					isRunning = false;
            					updateButtonStatus("At Surface");
            					break;
            			}
            		}
            	}
            }
        } // Buttons
    }
    OkayCancelDialog {
        id: dlgOkayCancel
        property variant btn
        onAccepted: {
            var previousButtons = {"At Surface": "Retrieval",
                                    "Retrieval": "First Bite",
                                    "First Bite": "Begin Fishing",
                                    "Begin Fishing": "Start",
                                    "Start": null}
            switch (actionType) {
                case "edit":

                    break;
                case "delete":
                    var btnStr = btn.text.split("\n")[0];
                    var previousBtnStr = previousButtons[btnStr];
                    btn.text = btnStr + "\n";
                    drops.deleteOperationAttribute(operationId, "Angler Time", btnStr);
                    updateButtonStatus(previousBtnStr);

                    if (btnStr === "At Surface") {
                        var newTime = (new Date()).getTime();
                        var elapsedTime = formatTime((newTime - startSeconds)/1000);
                        lblElapsedTime.text = elapsedTime;
                        rtHooks.enabled = false;
                        isRunning = true;
                        startTimer();
                    } else if (btnStr === "Start") {
                        lblElapsedTime.text = "00:00";
                        isRunning = false;
                        rtHooks.enabled = false;
                    }

                    break;
                case "move":

                    break;
                case "swap":

                    break;
            }
            stateMachine.dropTimeState = "enter";
        }
        onRejected: {
            stateMachine.dropTimeState = "enter";
        }
    } // dlgOkayCancel
    EditTimeDialog {
        id: dlgEditTime
        onAccepted: {
            console.info('new time: ' + numPad.tfMinutes.text + ":" + numPad.tfSeconds.text);
            console.info('btn: ' + editedButton.text);
            var newTime = numPad.tfMinutes.text + ":" + numPad.tfSeconds.text;
            var buttonType = editedButton.text.split("\n")[0]
            editedButton.text = buttonType + "\n" + newTime;
            drops.upsertOperationAttribute(operationId, luType, buttonType, valueType, newTime, "Angler " + anglerLetter);
            stateMachine.dropTimeState = "enter";
        }
        onRejected: {
            stateMachine.dropTimeState = "enter";
        }
    } // dlgEditTime

    HookMatrixStateMachine {
        id: hmSM
    } // hmSM - HookMatrixStateMachine
}