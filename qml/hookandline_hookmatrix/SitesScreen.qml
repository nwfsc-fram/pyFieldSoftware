import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0

Item {

    Connections {
        target: labelPrinter
        onPrinterStatusReceived: receivedPrinterStatus(comport, success, message)
    }
    function receivedPrinterStatus(comport, success, message) {
    // #267: Dialog used by both test print (SettingsScreen.qml) and tag print (HooksScreen.qml)
        var result = success ? "success" : "failed"
        dlgOkay.message = "Print job to " + comport + " status: " + result;
        if (result === "failed") {
            dlgOkay.action = "Please try again";
        } else {
            dlgOkay.action = "Well done, continue on matey";
        }
        dlgOkay.open();
    }

    Header {
        id: framHeader
        title: stateMachine.vessel ? stateMachine.vessel + " Sites" : "Sites"
        forwardTitle: "Drops"
        backButton.visible: false
        height: 50
    }
    BackdeckTableView {
        id: tvSites
        anchors.top: framHeader.bottom
        anchors.topMargin: 20
        anchors.left: parent.left
        anchors.leftMargin: 50
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        anchors.right: clFilter.left
        anchors.rightMargin: 20
//        anchors.horizontalCenter: parent.horizontalCenter
        width: 800;
//        height: 600;
        model: sites.sitesModel

        TableViewColumn {
            role: "setId"
            title: "Set ID"
            width: 140
        } // setId
        TableViewColumn {
            role: "siteName"
            title: "Site Name"
            width: 120
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // siteName
        TableViewColumn {
            role: "area"
            title: "Area"
            width: 200
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // area
        TableViewColumn {
            role: "dateTime"
            title: "Date Time"
            width: 210
            delegate: Text {
                text: styleData.value
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // dateTime
        TableViewColumn {
            role: "processingStatus"
            title: "Status"
            width: 100
            delegate: Text {
                text: styleData.value ? "Finished" : "Open"
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // processingStatus

        onClicked: {
            if (currentRow !== -1) {
                var item = sites.sitesModel.get(currentRow);
                if (item.processingStatus === "finished") {
                    var setId = item.setId;
                    dlgOkayCancel.message = "Set ID " + setId + " is finished."
                    dlgOkayCancel.action = "Do you wish to reopen it?"
                    dlgOkayCancel.accepted_action = "open site";
                    dlgOkayCancel.open();
                } else {
                    stateMachine.setId = sites.sitesModel.get(currentRow).setId;
                    stateMachine.site = sites.sitesModel.get(currentRow).siteName;
                    stateMachine.area = sites.sitesModel.get(currentRow).area;
                    stateMachine.siteDateTime = sites.sitesModel.get(currentRow).dateTime;
                    stateMachine.siteOpId = sites.sitesModel.get(currentRow).opId;
                    smHookMatrix.to_drops_state();
                }
            }
        }
    } // tvSites
    ColumnLayout {
        id: clFilter
        anchors.top: tvSites.top
        anchors.right: parent.right
        anchors.rightMargin: 20
        spacing: 20
        BackdeckButton {
            id: btnRetrieveSites
            text: qsTr("Retrieve\nSites");
            Layout.preferredWidth: 120;
            Layout.preferredHeight: 60;
            onClicked: {
                var filter;
                if (btnDaily.checked) filter = "today";
                else if (btnTwoDays.checked) filter = "yesterday";
                else filter = "all";
                sites.sitesModel.retrieveSites(filter);
            }
        } // btnRetrieveSites
        Rectangle {
//            Layout.topMargin: 10
//            Layout.bottomMargin: 10
            anchors {
                left: btnRetrieveSites.left
                right: btnRetrieveSites.right
            }
            height: 2
            color: "gray"
        }
        Text {
            id: txFilter
            horizontalAlignment: Text.AlignHCenter
            Layout.preferredWidth: 120
            text: qsTr("Filter")
            font.pixelSize: 24
        } // txFilter
        ExclusiveGroup { id: egFilter }
        BackdeckButton {
            id: btnDaily
            text: qsTr("Today's\nSites")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            exclusiveGroup: egFilter
            checkable: true
            checked: true
            onClicked: {
                sites.sitesModel.retrieveSites("today");
            }
        } // btnDaily
        BackdeckButton {
            id: btnTwoDays
            text: qsTr("Last Two\nDays Sites")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            exclusiveGroup: egFilter
            checkable: true
            checked: false
            onClicked: {
                sites.sitesModel.retrieveSites("yesterday");
            }
        } // btnTwoDays
        BackdeckButton {
            id: btnAll
            text: qsTr("All Sites")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            exclusiveGroup: egFilter
            checkable: true
            checked: false
            onClicked: {
                sites.sitesModel.retrieveSites("all");
            }
        } // btnAll
        Rectangle {
            Layout.topMargin: 10
            Layout.bottomMargin: 10
            anchors {
                left: btnRetrieveSites.left
                right: btnRetrieveSites.right
            }
            height: 2
            color: "gray"
        }
        BackdeckButton {
            id: btnSettings
            text: qsTr("Settings\n>>")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            onClicked: {
                smHookMatrix.to_settings_state();
            }
        } // btnSettings, https://github.com/nwfsc-fram/pyFieldSoftware/issues/259
    }
    Footer {
        id: framFooter
        height: 50
        state: "sites"
    }
    OkayCancelDialog {
        id: dlgOkayCancel
        onAccepted: {
            switch (accepted_action) {
                case "open site":
                    if (tvSites.currentRow !== -1) {
                        var item = sites.sitesModel.get(tvSites.currentRow)
                        stateMachine.setId = item.setId;
                        stateMachine.site = item.siteName;
                        stateMachine.area = item.area;
                        stateMachine.siteDateTime = item.dateTime;
                        stateMachine.siteOpId = item.opId;
                        sites.reopenSite(tvSites.currentRow, stateMachine.siteOpId);
                        smHookMatrix.to_drops_state();
                    }
                    break;
            }
        }
    }
    OkayDialog { id: dlgOkay }
}
