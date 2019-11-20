import QtQuick 2.7
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4
import QtQuick.Dialogs 1.2


import "." // For ScreenUnits

Dialog {
    id: dlgSinkerWeight
    title: qsTr("Sinker Weight (lbs)")
    width: 360
    height: 620
    property int weight: 5

    property int buttonHeight: 80
    property int buttonWeight: buttonHeight * 2
    property int fontSize: 20

    signal resultCaptured(int result);

    signal setWeight(int value)
    onSetWeight: {
        weight = value;
        switch (value) {
            case 1:
                btn1.checked = true;
                break;
            case 2:
                btn2.checked = true;
                break;
            case 3:
                btn3.checked = true;
                break;
            case 4:
                btn4.checked = true;
                break;
            case 5:
                btn5.checked = true;
                break;
        }
    }

    onAccepted: { resultCaptured(weight); }

    contentItem: Rectangle {
        color: "#eee"
        ExclusiveGroup { id: egSinkerWeights }
        ColumnLayout {
            spacing: 30
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            ColumnLayout {
                spacing: 20
                anchors.horizontalCenter: parent.horizontalCenter
                BackdeckButton {
                    id: btn1
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    text: qsTr("1 lb")
                    checkable: true
                    checked: false
                    exclusiveGroup: egSinkerWeights
                    onClicked: {
                        weight = 1;
                    }
                } // btn1
                BackdeckButton {
                    id: btn2
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    text: qsTr("2 lbs")
                    checkable: true
                    checked: false
                    exclusiveGroup: egSinkerWeights
                    onClicked: {
                        weight = 2;
                    }
                } // btn2
                BackdeckButton {
                    id: btn3
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    text: qsTr("3 lbs")
                    checkable: true
                    checked: false
                    exclusiveGroup: egSinkerWeights
                    onClicked: {
                        weight = 3;
                    }
                } // btn3
                BackdeckButton {
                    id: btn4
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    text: qsTr("4 lbs")
                    checkable: true
                    checked: false
                    exclusiveGroup: egSinkerWeights
                    onClicked: {
                        weight = 4;
                    }
                } // btn4
                BackdeckButton {
                    id: btn5
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    text: qsTr("5 lbs")
                    checkable: true
                    checked: false
                    exclusiveGroup: egSinkerWeights
                    onClicked: {
                        weight = 5;
                    }
                } // btn5
            }
            RowLayout {
                spacing: 20
                BackdeckButton {
                    id: btnOkay
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    text: qsTr("Okay")
                    onClicked: {
                        dlgSinkerWeight.accept();
                    }
                } // btnOkay
                BackdeckButton {
                    id: btnCancel
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    text: qsTr("Cancel")
                    onClicked: {
                        dlgSinkerWeight.close();
                    }
                } // btnCancel
            }
        }
    }
}

