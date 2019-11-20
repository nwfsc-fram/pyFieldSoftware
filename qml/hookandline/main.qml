import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
//import io.thp.pyotherside 1.5

//import "../common"

ApplicationWindow {
    title: qsTr("Field Collector - Hook and Line Survey")
    width: 1366
    height: 600
    visible: true
/*
    Python {
        Component.onCompleted: {

            // Add the directory of this .qml file to the search path
//            addImportPath(Qt.resolvedUrl('.'));
//            addImportPath(Qt.resolvedUrl('py'))

            // Asynchronous module importing
//            importModule('os', function() {
//                console.log('Python module "os" is now imported');
//                call('os.listdir', ['fieldCollector'], function(result) {
//                    console.log('dir listing: ' + result);
//                });
//            });

//            importModule('fieldCollector.plotorama', function () {
//                main.input1.text = '4.3,5.5,3.3,2.2,1.4,1.3,1.2,0.7,0.2';
//            });
        }

        onError: {
            console.log('We have an error: ' + traceback)
        }
    }
*/
/*
    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")
            MenuItem {
                text: qsTr("&New Site Collection")
                iconSource: "qrc:/resources/images/new.png"
                shortcut: StandardKey.New
            }

            MenuItem {
                text: qsTr("&Open Site Collection")
                onTriggered: messageDialog.show(qsTr("Open action triggered"));
                shortcut: StandardKey.Open
                iconSource: "qrc:/resources/images/open.png"
            }

            MenuSeparator {}
            MenuItem {
                text: qsTr("&Save Site Collection")
                iconSource: "qrc:/resources/images/save.png"
                shortcut: StandardKey.Save
            }
            MenuSeparator {}

            MenuItem {
                text: qsTr("E&xit")
                shortcut: StandardKey.Quit
                onTriggered: Qt.quit();
            }
        }
        Menu {
            title: qsTr("View")
            MenuItem {
                text: qsTr("Map View")
                onTriggered: main.togglePanel()
                iconSource: "qrc:/resources/images/map.png"
            }
        }

        Menu {
            title: qsTr("Queries")
        }

        Menu {
            title: qsTr("Utilities")
            MenuItem {
                text: qsTr("Sensor Feeds Setup")
                onTriggered: sdf.show()
            }
            MenuItem {
                text: qsTr("Data Sets Updates")
            }
            MenuItem {
                text: qsTr("Preferences")
            }
        }

        Menu {
            title: qsTr("Help")
            MenuItem {
                text: qsTr("Check for Updates")
                onTriggered: messageDialog.show(qsTr("Checking for updates...None"))
            }
            MenuItem {
                text: qsTr("About")
                onTriggered: messageDialog.show(qsTr("Field Collector 2.0"))
            }
        }
    }
*/

    toolBar:ToolBar {
        RowLayout {
            anchors.fill: parent
/*
            ToolButton {
                id: btnSaveCollection
                iconSource: "qrc:/resources/images/save.png"
                tooltip: "Save Site Collection"
            }
*/
            ToolButton {
                id: btnNewCollection
                iconSource: "qrc:/resources/images/new.png"
                tooltip: "Start New Site"
                onClicked: {}
            }
            ToolButton {
                id: btnOpenCollection
                iconSource: "qrc:/resources/images/open.png"
                tooltip: "Open Previous Site"
                onClicked: {}
            }
            ToolButton {
                id: btnSensorDataFeeds
                iconSource: "qrc:/resources/images/lightning-bolt.png"
                tooltip: "Open Sensor Data Feeds"
                onClicked: sdf.show()
            }

            ToolButton {
                id: btnMapView
                iconSource: "qrc:/resources/images/map2.png"
                onClicked: main.togglePanel()
                tooltip: "Toggle Map View"
            }
            ToolButton {
                id: btnSettings
                iconSource: "qrc:/resources/images/settings.png"
                tooltip: "Settings"
            }

            Item { Layout.fillWidth: true }

            Label {
                id: lblCurrentTime
                text: qsTr("Current Time")
                Layout.preferredWidth: 60
            } // lblCurrentTime
            TextField {
                id: tfCurrentTime
                text:
                Layout.preferredWidth: 80
                readOnly: true
            }  // tfCurrentTime
/*

            CheckBox {
                text: "Enabled"
                checked: true
                Layout.alignment: Qt.AlignRight
            }
*/
        }

    }

    SensorDataFeeds {
        id: sdf
   }

    MainForm {
        id: main
        anchors.rightMargin: 0
        anchors.bottomMargin: 0
        anchors.leftMargin: 0
        anchors.topMargin: 0
        anchors.fill: parent
//        input1.onTextChanged: image.source = 'image://python/' + input1.text
//        button1.onClicked: togglePanel(button1.text)

        function togglePanel() {
            if (rightPanel.visible) {
                rightPanel.visible = false
//                button1.text = 'Show Map'
            } else {
                rightPanel.visible = true
//                button1.text = 'Hide Map'
            }
        }

//        button1.onClicked: messageDialog.show(qsTr("Button 1 pressed"))
//        button2.onClicked: messageDialog.show(qsTr("Button 2 pressed"))
//        button3.onClicked: messageDialog.show(qsTr("Button 3 pressed"))
    }

    MessageDialog {
        id: messageDialog
        title: qsTr("May I have your attention, please?")

        function show(caption) {
            messageDialog.text = caption;
            messageDialog.open();
        }
    }

    State {
        name: "State1"
//        when:

        PropertyChanges {
            target: main.input1
            height: 13
            anchors.leftMargin: 0
            anchors.topMargin: 0
            anchors.rightMargin: 85
        }

        PropertyChanges {
            target: main.image
            x: 119
            y: 138
            width: 181
            height: 162
            opacity: 1
        }

//        PropertyChanges {
//            target: main.image
//            anchors.leftMargin:
//        }
    }

}
