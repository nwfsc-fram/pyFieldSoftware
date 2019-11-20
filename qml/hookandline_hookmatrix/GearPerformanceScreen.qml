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
                btnLostHooks.checked = false;
                btnLostGangion.checked = false;
                btnLostSinker.checked = false;
                btnMinorTangle.checked = false;
                btnMajorTangle.checked = false;
                btnUndeployed.checked = false;
                btnExclude.checked = false;

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
                btnNoProblems.checked = false;

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
                btnNoProblems.checked = false;

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
                btnNoProblems.checked = false;

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
                btnNoProblems.checked = false;
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
                btnNoProblems.checked = false;
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
                btnNoProblems.checked = false;
                if (checked)
                    gearPerformance.addGearPerformance("Undeployed");
                else
                    gearPerformance.deleteGearPerformance("Undeployed");
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
                btnNoProblems.checked = false;
                if (checked)
                    gearPerformance.addGearPerformance("Exclude");
                else
                    gearPerformance.deleteGearPerformance("Exclude");

            }
        } // btnNoProblems
//        	-- No Problems (default value - use this if no performance issues identified)
//	-- Lost Hook(s) -- Lost Gangion  -- Lost Sinker  -- Minor Tangle  -- Major Tangle  -- Undeployed

    } // clPerformances

    Footer {
        id: framFooter
        height: 50
        state: "gear performance"
    }
}