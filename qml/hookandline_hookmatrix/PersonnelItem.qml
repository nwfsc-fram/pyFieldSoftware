import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.2

Item {
    property string personnelName: "Angler A"
    property alias tfPersonnel: tfPersonnel
    property string tfColor: "lightgray"

    signal currentPersonnelChanged(string personnelName);

    implicitWidth: clPerson.implicitWidth
    implicitHeight: clPerson.implicitHeight

    ColumnLayout {
        id: clPerson
        spacing: 0
        Label {
            text: personnelName
            font.pixelSize: 24
            horizontalAlignment: Text.AlignHCenter
            Layout.preferredWidth: 260
            Layout.preferredHeight: 40
        }
        RowLayout {
            spacing: 10
            BackdeckButton {
                text: qsTr("X")
                Layout.preferredWidth: 60
                Layout.preferredHeight: 60
                onClicked: {
                    tfPersonnel.text = ""
                    tfPersonnel.forceActiveFocus();
                    currentPersonnelChanged(personnelName);
                }
            } // X
            TextField {
                id: tfPersonnel
                placeholderText: personnelName
                font.pixelSize: 24
                Layout.preferredWidth: 200
                Layout.preferredHeight: 60
                MouseArea {
                    anchors.fill: parent
                    onClicked:{
                        parent.selectAll();
                        parent.forceActiveFocus();
                        currentPersonnelChanged(personnelName);
                        tfColor = "white"
                    }
                }
            } // tfPersonnel
        }
    }

}