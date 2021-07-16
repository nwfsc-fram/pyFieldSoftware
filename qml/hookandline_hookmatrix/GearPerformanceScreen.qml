import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

Item {

    property int buttonHeight: 80;
    property int buttonWidth: 2 * buttonHeight;
    property variant anglerOpId: gearPerformance.getAnglerOpId()
    property variant isAnglerDoneFishing: drops.isAnglerDoneFishing(anglerOpId)

    Connections {
        target: gearPerformance
        onGearPerformanceSelected: populateGearPerformanceInfo(results);
    } // gearPerformance.onGearPerformanceSelected
    function populateGearPerformanceInfo(results) {
        var stop_processing = false;
        for (var x in results) {
            switch (results[x]) {
                case "No Problems":
                    btnNoProblems.checked = true;
                    stop_processing = true;
                    break;
                case "Lost Hooks":
                    btnLostHooks.checked = true;
                    break;
                case "Lost Gangion":
                    btnLostGangion.checked = true;
                    break;
                case "Lost Sinker":
                    btnLostSinker.checked = true;
                    break;
                case "Minor Tangle":
                    btnMinorTangle.checked = true;
                    break;
                case "Major Tangle":
                    btnMajorTangle.checked = true;
                    break;
                case "Undeployed":
                    btnUndeployed.checked = true;
                    break;
                case "Exclude":
                    btnExclude.checked = true;
                    break;
            }
            if (stop_processing) break;
        }
    }
    Header {
        id: framHeader
        title: "Gear Performance: Drop " + stateMachine.drop + " - Angler " + stateMachine.angler
        height: 50
        backwardTitle: "Drops"
        forwardTitle: drops.getAnglerHooksLabel(anglerOpId, true)
        forwardEnabled: drops.isAnglerDoneFishing(anglerOpId)
        forwardVisible: drops.isAnglerDoneFishing(anglerOpId)
    }
    ColumnLayout {
        id: clNoProblems
        spacing: 20
        anchors.right: clPerformances.left
        anchors.rightMargin: 100
        anchors.verticalCenter: parent.verticalCenter
        // #239: Bind onCheckedChange to addGearPerformance/deleteGearPerformance to just interact with btn.checked
        BackdeckButton {
            id: btnNoProblems
            text: qsTr("No Problems")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    btnLostHooks.checked = false;
                    btnLostGangion.checked = false;
                    btnLostSinker.checked = false;
                    btnMinorTangle.checked = false;
                    btnMajorTangle.checked = false;
                    btnUndeployed.checked = false;
                    btnExclude.checked = false;
                }
            }
            onCheckedChanged: {  // add to DB anytime checked, remove anytime unchecked
                if (checked) gearPerformance.addGearPerformance(text)
                else gearPerformance.deleteGearPerformance(text)
            }
        } // btnNoProblems
//        	-- No Problems (default value - use this if no performance issues identified)
//	-- Lost Hook(s) -- Lost Gangion  -- Lost Sinker  -- Minor Tangle  -- Major Tangle  -- Undeployed

    } // clPerformances
    ColumnLayout {
        id: clPerformances
        spacing: 20
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        BackdeckButton {
            id: btnLostHooks
            text: qsTr("Lost Hooks")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    btnNoProblems.checked = false;
                    btnUndeployed.checked = false;
                }
            }
            onCheckedChanged: {  // add to DB anytime checked, remove anytime unchecked
                if (checked) gearPerformance.addGearPerformance(text)
                else gearPerformance.deleteGearPerformance(text)
            }
        } // btnLostHooks
        BackdeckButton {
            id: btnLostGangion
            text: qsTr("Lost Gangion")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    btnNoProblems.checked = false;
                    btnUndeployed.checked = false;
                    btnLostSinker.checked = true // #145: auto-select lost sinker whenever lost gangion is selected
                }
            }
            onCheckedChanged: {  // add to DB anytime checked, remove anytime unchecked
                if (checked) gearPerformance.addGearPerformance(text)
                else gearPerformance.deleteGearPerformance(text)
            }
        } // btnLostGangion
        BackdeckButton {
            id: btnLostSinker
            text: qsTr("Lost Sinker")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    btnNoProblems.checked = false;
                    btnUndeployed.checked = false;
                }
                else {
                    // #145: auto-unselect lost gangion whenever lost sinker is unselected
                    btnLostGangion.checked = false
                }
            }
            onCheckedChanged: {  // add to DB anytime checked, remove anytime unchecked
                if (checked) gearPerformance.addGearPerformance(text)
                else gearPerformance.deleteGearPerformance(text)
            }
        } // btnLostSinker
        BackdeckButton {
            id: btnMinorTangle
            text: qsTr("Minor\nTangle")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    btnNoProblems.checked = false;
                    btnUndeployed.checked = false;
                }
            }
            onCheckedChanged: {  // add to DB anytime checked, remove anytime unchecked
                if (checked) gearPerformance.addGearPerformance("Minor Tangle")
                else gearPerformance.deleteGearPerformance("Minor Tangle")
            }
        } // btnMinorTangle
        BackdeckButton {
            id: btnMajorTangle
            text: qsTr("Major\nTangle")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    btnNoProblems.checked = false;
                    btnUndeployed.checked = false;
                }
            }
            onCheckedChanged: {  // add to DB anytime checked, remove anytime unchecked
                if (checked) gearPerformance.addGearPerformance("Major Tangle")
                else gearPerformance.deleteGearPerformance("Major Tangle")
            }
        } // btnMajorTangle
        BackdeckButton {
            id: btnUndeployed
            text: qsTr("Undeployed")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                if (checked) {
                    // deselect all gp buttons
                    btnNoProblems.checked = false;
                    btnLostHooks.checked = false;
                    btnLostGangion.checked = false;
                    btnLostSinker.checked = false;
                    btnMinorTangle.checked = false;
                    btnMajorTangle.checked = false;
                    btnExclude.checked = true;  // #239: Auto-select exclude when undeployed selected
                    dlgUndeployed.open()  // #144: ask to autopop hooks and times to Undeployed
                }
            }
            onCheckedChanged: {  // add to DB anytime checked, remove anytime unchecked
                if (checked) gearPerformance.addGearPerformance(text)
                else gearPerformance.deleteGearPerformance(text)
            }
        } // btnUndeployed

    }
    ColumnLayout {
        id: clExclude
        spacing: 20
        anchors.left: clPerformances.right
        anchors.leftMargin: 100
        anchors.verticalCenter: parent.verticalCenter

        BackdeckButton {
            id: btnExclude
            text: qsTr("Exclude")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                if (!checked) {
                    btnUndeployed.checked = false
                }
            }
            onCheckedChanged: {  // add to DB anytime checked, remove anytime unchecked
                if (checked) gearPerformance.addGearPerformance(text)
                else gearPerformance.deleteGearPerformance(text)
            }
        }
//        	-- No Problems (default value - use this if no performance issues identified)
//	-- Lost Hook(s) -- Lost Gangion  -- Lost Sinker  -- Minor Tangle  -- Major Tangle  -- Undeployed

    } // clPerformances
    OkayCancelDialog {
        // #144: auto-populate hooks 1-5 as Undeployed when undeployed option clicked
        id: dlgUndeployed
        message: '"Undeployed" gear perf. selected.'
        action: 'Set all Angler ' + stateMachine.angler + ' hooks and times to "Undeployed"?'
        btnOkay.text: "Yes"
        btnCancel.text: "No"
        onAccepted: {
            gearPerformance.undeployAnglerTimes()  // empty time vals to 'UN'; do this first for enabling hooks nav race
            gearPerformance.upsertHooksToUndeployed()  // set all hooks to undeployed
            framHeader.forwardTitle = drops.getAnglerHooksLabel(anglerOpId, true)  // update Hooks header text
            framHeader.forwardVisible = true  // make nav to hooks visible
            framHeader.forwardEnabled = true  // enable nav to hooks
        }
        onRejected: {}
    }
    Footer {
        id: framFooter
        height: 50
        state: "gear performance"
    }
}