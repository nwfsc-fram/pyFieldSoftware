import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.1
import QtQml.Models 2.2
import QtQuick.Controls.Styles 1.4

ApplicationWindow {
    title: "Sensor Data Feeds"
    width: 1024
    height: 768
    visible: false

    SplitView {
        id: splitView1
        x: 0
        y: 0
        width: parent.width
        height: parent.height

        Rectangle {
            id: leftPanel
            width: 300

            ListModel {
                id: sensorConfigModel
                ListElement {
                    equipment: "Garmin GPS 152"
                }
                ListElement {
                    equipment: "Furuno SC30"
                }
            }

//            ListModel {
//                id: sensorConfigModel
//                ListElement {
//                    equipment: "GPS 152"
//                    sentences: [
//                        ListElement {
//                            sentence: "$GPRMC"
//                            measurements: [
//                                ListElement {
//                                    measurement: "Latitude"
//                                    uom: "Deg-Min"
//                                },
//                                ListElement {
//                                    measurement: "Longitude"
//                                    uom: "Deg-Min"
//                                }
//                            ]
//                        },
//                        ListElement {
//                            sentence: "$GPHDT"
//                        }
//                    ]
//                }
//                ListElement {
//                    equipment: "SC30"
//                }
//            }

//            Component {
//                id: sensorConfigDelegate
//                Item {
//                    width: 200; height: 50
//                    Text { id: equipmentField; text: equipment }
//                    Row {
//                        anchors.top: equipmentField.bottom
//                        spacing: 5
//                        Text { text: "Sentences:" }
//                        Repeater {
//                            model: sentences
//                            Text { text: sentence }
//                        }
//                    }
//                }
//            }

            TreeViewStyle {
                id: sensorTreeViewStyle
                indentation: 4
            }

            TreeView {
                width: parent.width
                TableViewColumn {
                    title: "Equipment"
                    role: "equipment"
                    width: parent.width
                }
                model: sensorConfigModel
            }



        }

        Rectangle {
            id: centerPanel
            Layout.fillWidth: true
        }
//        MapView {
//            Layout.fillWidth: true
//        }
    }

}

