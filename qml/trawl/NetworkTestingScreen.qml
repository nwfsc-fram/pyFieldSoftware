import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Item {

    Component.onCompleted: {

        // Select the proper printer according to settings.selectedPrinter
        if ((settings.currentPrinter == undefined) || (settings.currentPrinter == null)) {
            if ("Printer 1" in serialPortManager.printers) {
                settings.currentPrinter = serialPortManager.printers["Printer 1"]
                btnPrinter1.checked = true;
            }
        } else {
            if (btnPrinter1.text.indexOf(settings.currentPrinter) != -1) {
                btnPrinter1.checked = true;
            } else {
                btnPrinter2.checked = true;
            }
        }
    }

    Component.onDestruction: {
        tbdSM.to_home_state()
    }

    Connections {
        target: networkTesting
        onPrinterStatusReceived: processPrinterStatus(comport, success, message)
    }

    function processPrinterStatus(comport, success, message) {
        var wrapped_message = stringDivider(message, 25, "", "\n")
        lblPrintResult.text = wrapped_message;
    }

    function stringDivider(str, width, prefix, postfix) {
        if (str.length>width) {
            var p=width
            for (;p>0 && !/\s/.test(str[p]); p--) {
            }
            if (p>0) {
                var left = str.substring(0, p);
                var right = str.substring(p+1);
                return prefix + left + postfix + stringDivider(right, width, prefix, postfix);
            }
        }
        return prefix+str+postfix;
    }

    GridLayout {
        x: 40
        y: 40
        columns: 2
        rows: 2
        columnSpacing: 100
        rowSpacing: 20


        Label {
            id: lblItems
            text: "Tests"
            anchors.horizontalCenter: parent.center
            font.pixelSize: 24
            font.bold: true
        }
        Label {
            id: lblResult
            text: "Results"
            anchors.horizontalCenter: parent.center
            font.pixelSize: 24
            font.bold: true
        }

        RowLayout {
            id: rlyPrintTest
            spacing: 20
            anchors.top: lblItems.bottom
            anchors.topMargin: 20

            ExclusiveGroup {
                id: egPrinters
            }
            Label {
                id: lblPrintTesting
                text: "Printer Testing"
                font.pixelSize: 24
            }

            TrawlBackdeckButton {
                id: btnPrinter1
                text: "Printer 1\n(" + serialPortManager.printers["Printer 1"] + ")"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checked: true
                checkable: true
                exclusiveGroup: egPrinters
                onClicked: {
                    settings.currentPrinter = serialPortManager.printers["Printer 1"]
                }
            } // btnPrinter1
            TrawlBackdeckButton {
                id: btnPrinter2
                text: "Printer 2\n(" + serialPortManager.printers["Printer 2"] + ")"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                checked: false
                checkable: true
                exclusiveGroup: egPrinters
                onClicked: {
                    settings.currentPrinter = serialPortManager.printers["Printer 2"]
                }

            } // btnPrinter2
            TrawlBackdeckButton {
                id: btnPrint
                text: "Test Print"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: {
                    var comport = btnPrinter1.checked ? serialPortManager.printers["Printer 1"] :
                                                        serialPortManager.printers["Printer 2"]
                    networkTesting.printTestLabel(comport)
                }
            } // btnPrint
        }
        Label {
            id: lblPrintResult
            text: "Print Result"
            font.pixelSize: 24
        }


    }

    TrawlBackdeckButton {
        text: qsTr("Done")
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        onClicked: screens.pop()
    }
}