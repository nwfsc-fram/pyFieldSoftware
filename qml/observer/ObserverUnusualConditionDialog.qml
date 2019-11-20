import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "codebehind/HelperFunctions.js" as HelperFunctions
import "../common" // For TrawlBackdeckButton

// Dialog to alert observer to an unusual OPTECS condition that should be reported
// to the NOAA WCGOP Observer Program.

Dialog {
    id: dlg
    width: 750
    height: 400
    title: "Unusual OPTECS Condition"

    property string datetime: ""
    property string summary: ""
    property string optecs_email_alias: "nmfs.nwfsc.wcgop.optecs@noaa.gov"

    function open(summary) {
        console.info("Unusual condition!!!!");
        //console.trace();
        dlg.datetime = HelperFunctions.dateTodayString();
        dlg.summary = summary;
        visible = true;
    }

    contentItem: Rectangle {
        color: "#eee"
        ColumnLayout {
            id: colLightning
            Layout.preferredWidth: 150
            Layout.preferredHeight: parent.height
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            Image {
                id: lightningBolt
                // N.B. If image png is changed, remember to include in observer.qrc
                source: 'qrc:/resources/images/lightning_yellow.png'
                horizontalAlignment: Image.AlignHCenter
                verticalAlignment: Image.AlignVCenter
            }
        }
        ColumnLayout {
            id: colMainBody
            anchors.left: colLightning.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            Layout.preferredWidth: parent.width - colLightning.width
            Layout.preferredHeight: parent.height
            RowLayout {
                id: rowMessage
                Layout.preferredWidth: colMainBody.width
                Layout.preferredHeight: colMainBody.height - rowOK.height
                anchors.left: colMainBody.left
                anchors.right: colMainBody.right
                anchors.leftMargin: 10
                Label {
                    id: lblMessage
                    text: "\n" +
                            "An unusual OPTECS condition has occurred.\n" +
                            "\n" +
                            "Summary: " + dlg.summary + "\n" +
                            "DateTime: " + dlg.datetime + "\n\n" +
                            "Please send email to " + optecs_email_alias + "\n" +
                            "including the name of your tablet, the summary and datetime above,\n" +
                            "and details about the operation in progress.\n" +
                            "\n" +
                            "The current operation may be in a confused state.\n" +
                            "Please restart the application at your earliest convenience."
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    horizontalAlignment: Text.AlignLeft
                    font.pixelSize: 20
                }
            }
            RowLayout {
                id: rowOK
                Layout.preferredWidth: colMainBody.width
                Layout.preferredHeight: 75
                anchors.bottom: colMainBody.bottom
                anchors.left: colMainBody.left
                anchors.right: colMainBody.right
                anchors.leftMargin: 10
                TrawlBackdeckButton {
                    id: btnOkay
                    text: "OK"
                    x: dlg.width / 3
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: 50
                    onClicked: { dlg.accept(); }
                } // btnOkay
            }
        } // ColumnLayout for text and OK button

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
