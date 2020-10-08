import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

Item {

    property int buttonHeight: 80;
    property int buttonWidth: 2 * buttonHeight;

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

    function updateButtonRelations(clickedBtnStr) {
        // central place for logic regarding how buttons interact with each other
        var btnGpMap = {
            "No Problems": btnNoProblems,
            "Lost Hooks": btnLostHooks,
            "Lost Gangion":  btnLostGangion,
            "Lost Sinker": btnLostSinker,
            "Minor Tangle": btnMinorTangle,
            "Major Tangle": btnMajorTangle,
            "Undeployed": btnUndeployed,
            "Exclude": btnExclude
        };
        for (var gpStr in btnGpMap) {  // loop through each button once per func call
            var btnObj = btnGpMap[gpStr]
            if (clickedBtnStr === "No Problems" ) {
                if(gpStr !== clickedBtnStr) {  // deselect and delete everything except clickedBtnStr
                    btnObj.checked = false;
                    gearPerformance.deleteGearPerformance(gpStr);
                }
            } else if (clickedBtnStr === "Undeployed") {  // always select exclude w undeployed
                if(gpStr === "Exclude") {
                    btnObj.checked = true;
                    gearPerformance.addGearPerformance(gpStr);
                } else if(gpStr !== clickedBtnStr) {
                    btnObj.checked = false;
                    gearPerformance.deleteGearPerformance(gpStr);
                }
            } else { // start by deselecting und, no probs if anything else is checked
                if (gpStr === "Undeployed" || gpStr === "No Problems" ) {
                    btnObj.checked = false;
                    gearPerformance.deleteGearPerformance(gpStr);
                }
                if (clickedBtnStr === "Lost Gangion" && btnGpMap[clickedBtnStr].checked == true) {
                    // sinker lost w gangion
                    if (gpStr === "Lost Sinker") {
                        btnObj.checked = true;
                        gearPerformance.addGearPerformance(gpStr)
                    }
                }
                if (clickedBtnStr === "Lost Sinker" && btnGpMap[clickedBtnStr].checked == false) {
                    // no lost sinker, no lost gangion
                    if (gpStr === "Lost Gangion") {
                        btnObj.checked = false;
                        gearPerformance.deleteGearPerformance(gpStr)
                    }
                }
            }
        }
    }

    Header {
        id: framHeader
        title: "Gear Performance: Drop " + stateMachine.drop + " - Angler " + stateMachine.angler
        height: 50
    }
    ColumnLayout {
        id: clNoProblems
        spacing: 20
        anchors.right: clPerformances.left
        anchors.rightMargin: 100
        anchors.verticalCenter: parent.verticalCenter
        BackdeckButton {
            id: btnNoProblems
            text: qsTr("No Problems")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            checkable: true
            checked: false
            onClicked: {
                updateButtonRelations(btnNoProblems.text)

                if (checked)
                    gearPerformance.addGearPerformance("No Problems");
                else
                    gearPerformance.deleteGearPerformance("No Problems");
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
                updateButtonRelations(btnLostHooks.text)

                if (checked)
                    gearPerformance.addGearPerformance("Lost Hooks");
                else
                    gearPerformance.deleteGearPerformance("Lost Hooks");

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
                updateButtonRelations(btnLostGangion.text)

                if (checked)
                    gearPerformance.addGearPerformance("Lost Gangion");
                else
                    gearPerformance.deleteGearPerformance("Lost Gangion");

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
                updateButtonRelations(btnLostSinker.text)

                if (checked)
                    gearPerformance.addGearPerformance("Lost Sinker");
                else
                    gearPerformance.deleteGearPerformance("Lost Sinker");
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
                updateButtonRelations(btnMinorTangle.text)
                if (checked)
                    gearPerformance.addGearPerformance("Minor Tangle");
                else
                    gearPerformance.deleteGearPerformance("Minor Tangle");
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
                updateButtonRelations(btnMajorTangle.text)
                if (checked)
                    gearPerformance.addGearPerformance("Major Tangle");
                else
                    gearPerformance.deleteGearPerformance("Major Tangle");
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
                updateButtonRelations(btnUndeployed.text)
                if (checked) {
                    gearPerformance.addGearPerformance("Undeployed");
                    dlgUndeployed.open();
                } else {
                    gearPerformance.deleteGearPerformance("Undeployed");
                }
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
                updateButtonRelations(clExclude.text)
                if (checked)
                    gearPerformance.addGearPerformance("Exclude");
                else
                    gearPerformance.deleteGearPerformance("Exclude");

            }
        } // btnNoProblems
//        	-- No Problems (default value - use this if no performance issues identified)
//	-- Lost Hook(s) -- Lost Gangion  -- Lost Sinker  -- Minor Tangle  -- Major Tangle  -- Undeployed

    } // clPerformances
    OkayCancelDialog {
        id: dlgUndeployed
        message: '"Undeployed" gear perf. selected.'
        lblAction.text: 'Set all Angler ' + stateMachine.angler + ' hooks to "Undeployed"?'
        btnOkay.text: "Yes"
        btnCancel.text: "No"
        onAccepted: { gearPerformance.setHooksToUndeployed() }
        onRejected: {}
    }
    Footer {
        id: framFooter
        height: 50
        state: "gear performance"
    }
}