import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 600
    height: 600
    title: "Select Release Method"

    property string releaseMethod: ""


    contentItem: Rectangle {
        color: "#eee"
        anchors.fill: parent
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 50
            Label {
                text: "Select Release Method"
                font.pixelSize: 20
            }

            GridLayout {
                id: rowHandlingMethod
                columns: 2
                ExclusiveGroup { id: rfGroup }
                Repeater {
                    id: rpttest

                    model: appstate.catches.RockfishHandlingMethods

                    ObserverGroupButton{
                        text: display
                        exclusiveGroup: rfGroup
                        checked: releaseMethod == display
                        onClicked: {
                            releaseMethod = display
                            releaseMethodDesc.text = appstate.catches.getHandlingMethodDesc(display)
                        }
                    }
                }
            }
            Label {
                id: releaseMethodDesc
                text: ""
                font.pixelSize: 24
            }
            RowLayout {
//                ObserverSunlightButton {
//                    Layout.preferredWidth: 180
//                    Layout.preferredHeight: 50
//                    text: "Cancel"
//                    Layout.rightMargin: 10

//                    onClicked: {
//                        releaseMethod = ""
//                        dlg.reject();
//                    }
//                }
                ObserverSunlightButton {
                    Layout.preferredWidth: 180
                    Layout.preferredHeight: 50
                    text: "Accept"
                    visible: releaseMethod != ""

                    onClicked: {
                        dlg.accept();
                    }
                }
            }
        }




        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
