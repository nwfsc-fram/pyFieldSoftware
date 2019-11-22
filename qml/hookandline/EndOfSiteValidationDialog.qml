import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2

Dialog {
    id: dlg
    width: 1280
    height: 900
    title: "End of Site Validation"

    modality: Qt.NonModal

    property variant setId: null
    property int tabItemOffset: 20;

    Component.onCompleted: {
        console.info((new Date()) + " - EndOfSiteValidationDialog.qml completed");
    }
    onVisibleChanged: {
        // If the dialog is closed, set the bestSpeciesClicked items to false
        if (!visible) {
        }
    }
    Connections {
        target: endOfSiteValidation.cutterStationModel
        onCutterRecorderChanged: setCutterStationRecorder(recordedBy)
    }
    function setCutterStationRecorder(recordedBy) {
        tabCutterStation.item.lblDopRecordedBy.text = recordedBy;
    }

    onRejected: {  }
    onAccepted: {  }

    contentItem: Rectangle {
        color: SystemPaletteSingleton.window(true)
        anchors.fill: parent
        ColumnLayout {
            Layout.preferredWidth: parent.width
            spacing: 20
            RowLayout {
                id: rlOperations
                anchors.top: parent.top
                anchors.topMargin: 10
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.right: parent.right
//                Layout.preferredWidth: dlg.width
                Label { text: "Select Operation" }
                ComboBox {
                    id: cbSetId
                    width: parent.width
                    anchors.verticalCenter: parent.verticalCenter
                    model: endOfSiteValidation.operationsModel
                    currentIndex: 0
                    onCurrentIndexChanged: {
                        if (currentIndex >= 0) {
                            setId = this.currentText;
                            endOfSiteValidation.loadOperation(setId);
                        }
                    }
                }
                Label { Layout.preferredWidth: 15 }
                Button {
                    id: btnReloadSite
                    text: "Reload Operation"
                    onClicked: {
                        endOfSiteValidation.loadOperation(cbSetId.currentText);
                    }
                }
            } // rlOperations
            TabView {
                id: tbPositions
                anchors.top: rlOperations.bottom
                anchors.topMargin: 20
                Layout.preferredWidth: dlg.width
                Layout.preferredHeight: dlg.height - rlOperations.height - 20

                style: TabViewStyle {
////                    frameOverlap: 1
//                    tab: Rectangle {
//                        color: styleData.selected ? "lightgray" : SystemPaletteSingleton.window(true)
//                        border.color:  styleData.selected ? "black" : "lightgray" //"steelblue"
//                        implicitWidth: 120
//                        implicitHeight: 30
//                        radius: 3
//                        Text {
//                            id: text
//                            font.pixelSize: 12
//                            anchors.centerIn: parent
//                            text: styleData.title
//                            color: styleData.enabled ? "black" : "#a8a8a8"
//                        }
//                    }
                    frame: Rectangle {
                        border.color: "gray"
                        color: SystemPaletteSingleton.window(true)
                    }
                }
                Tab {
                    id: tabHookLogger
                    title: qsTr("HookLogger");
                    active: true
                    anchors.fill: parent
                    Item {
                        x: tabItemOffset
                        y: tabItemOffset

                        property int geoWidth: 120
//                        Layout.preferredWidth: dlg.width - (2 * tabItemOffset)
//                        Layout.preferredHeight: parent.height - tabItemOffset - tabItemOffset
                        anchors.fill: parent
//                        ColumnLayout {
//                            GridLayout {
//                                id: glSiteOverview
//                                anchors.fill: parent
//                                columns: 7
//                                rows: 2
//                                columnSpacing: 20
//                                rowSpacing: 20
//                                Label { text: 'Set ID'}
//                            } // glSiteOverview

                            TableView {
                            id: tvHookLoggerEvents
                            headerVisible: true
                            height: 200
                            width: parent.width
//                            anchors.fill: parent
                            model: endOfSiteValidation.hookLoggerDropModel
                            TableViewColumn {
                                role: 'dropNumber'
                                title: 'Drop Number'
                                width: 80
                            } // dropNumber
                            TableViewColumn {
                                role: 'startTime'
                                title: 'Start Time'
                                width: 80
                            } // startTime
                            TableViewColumn {
                                role: 'startLatitude'
                                title: 'Start Latitude'
                                width: geoWidth
                            } // startLatitude
                            TableViewColumn {
                                role: 'startLongitude'
                                title: 'Start Longitude'
                                width: geoWidth
                            } // startLongitude
                            TableViewColumn {
                                role: 'startDepth'
                                title: 'Start Depth'
                                width: 80
                            } // startDepth
                            TableViewColumn {
                                role: 'endTime'
                                title: 'End Time'
                                width: 80
                            } // endTime
                            TableViewColumn {
                                role: 'endLatitude'
                                title: 'End Latitude'
                                width: geoWidth
                            } // endLatitude
                            TableViewColumn {
                                role: 'endLongitude'
                                title: 'End Longitude'
                                width: geoWidth
                            } // endLongitude
                            TableViewColumn {
                                role: 'endDepth'
                                title: 'End Depth'
                                width: 80
                            } // endDepth
                            TableViewColumn {
                                role: 'tideHeight'
                                title: 'Tide Height'
                                width: 80
                            } // tideHeight
                            TableViewColumn {
                                role: 'dropType'
                                title: 'Drop Type'
                                width: 80
                            } // dropType
                            TableViewColumn {
                                role: 'includeInSurvey'
                                title: 'Include ?'
                                width: 80
                            } // includeInSurvey
                            style: TableViewStyle {
                                itemDelegate: Rectangle {
                                    color: {
                                        styleData.value ? (styleData.row % 2 ? "white" : "whitesmoke") : "pink";
                                    }
                                    Text {
                                        text: styleData.value ? styleData.value : ""
                                        horizontalAlignment: Text.AlignHCenter
//                                        elide: Text.ElideRight
                                        renderType: Text.NativeRendering
                                    }
                                }
                            }
                        } // tvHookLoggerEvents
//                        }
                    }
                } // tabHookLogger
                Tab {
                    id: tabHookMatrix
                    title: qsTr("HookMatrix")
                    active: true
                    anchors.fill: parent

                    property int hookWidth: 100
                    property int timeWidth: 60

                    Item {
                        TableView {
                            id: tvHookMatrix
                            headerVisible: true
                            anchors.fill: parent
                            model: endOfSiteValidation.hookMatrixModel
                            TableViewColumn {
                                role: 'dropNumber'
                                title: 'Drop'
                                width: 40
//                                delegate: Text {
//                                    text: styleData.value ? styleData.value : ""
//                                    horizontalAlignment: Text.AlignHCenter
//                                }
                            } // dropNumber
                            TableViewColumn {
                                role: 'angler'
                                title: 'Angler'
                                width: 50
//                                delegate: Text {
//                                    text: styleData.value ? styleData.value : ""
//                                    horizontalAlignment: Text.AlignHCenter
//                                }
                            } // angler
                            TableViewColumn {
                                role: 'anglerName'
                                title: 'Angler Name'
                                width: 100
                            } // anglerName
                            TableViewColumn {
                                role: 'start'
                                title: 'Start'
                                width: timeWidth
                            } // start
                            TableViewColumn {
                                role: 'beginFishing'
                                title: 'Begin Fish'
                                width: timeWidth
                            } // beginFishing
                            TableViewColumn {
                                role: 'firstBite'
                                title: 'First Bite'
                                width: timeWidth
                            } // firstBite
                            TableViewColumn {
                                role: 'retrieval'
                                title: 'Retrieval'
                                width: timeWidth
                            } // retrieval
                            TableViewColumn {
                                role: 'atSurface'
                                title: 'At Surface'
                                width: timeWidth + 10
                            } // atSurface
                            TableViewColumn {
                                role: 'includeInSurvey'
                                title: 'Include?'
                                width: 60
                                delegate: Text {
                                    text: styleData.value ? styleData.value : ""
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            } // includeInSurvey
                            TableViewColumn {
                                role: 'gearPerformance'
                                title: 'Gear Performance'
                                width: 80
                            } // gearPerformance
                            TableViewColumn {
                                role: 'hook1'
                                title: 'Hook 1'
                                width: hookWidth
                            } // hook1
                            TableViewColumn {
                                role: 'hook2'
                                title: 'Hook 2'
                                width: hookWidth
                            } // hook2
                            TableViewColumn {
                                role: 'hook3'
                                title: 'Hook 3'
                                width: hookWidth
                            } // hook3
                            TableViewColumn {
                                role: 'hook4'
                                title: 'Hook 4'
                                width: hookWidth
                            } // hook4
                            TableViewColumn {
                                role: 'hook5'
                                title: 'Hook 5'
                                width: hookWidth
                            } // hook5
                            TableViewColumn {
                                role: 'sinkerWeight'
                                title: 'Sinker'
                                width: 50
//                                delegate: Text {
//                                    text: styleData.value ? styleData.value : ""
//                                    horizontalAlignment: Text.AlignHCenter
//                                }
                            } // sinkerWeight
                            TableViewColumn {
                                role: 'recordedBy'
                                title: 'Recorded By'
                                width: 90
                            } // recordedBy

                            style: TableViewStyle {
                                itemDelegate: Rectangle {
                                    color: {
                                        (styleData.value && styleData.value != "") ? (styleData.row % 2 ? "white" : "whitesmoke") : "pink";
                                    }
                                    Text {
                                        text: (styleData.value && styleData.value != "") ? styleData.value : ""
                                        horizontalAlignment: Text.AlignHCenter
//                                        elide: Text.ElideRight
                                        renderType: Text.NativeRendering
                                    }
                                }
                                headerDelegate: Rectangle {
                                    height: textItem.implicitHeight * 1.2
                                    width: textItem.implicitWidth
                                    gradient: Gradient {
                                        GradientStop { position: 0.0; color: "white" }
                                        GradientStop { position: 1.0; color: "lightgray" }
                                    }
                                    border.color: "lightgray"
                                    border.width: 1
                                    Text {
                                        id: textItem
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
//                                        horizontalAlignment: styleData.textAlignment
                                        horizontalAlignment: Text.AlignHLeft
                                        anchors.leftMargin: 12
                                        text: styleData.value
                                        elide: Text.ElideRight
                                        color: textColor
                                        renderType: Text.NativeRendering
                                        font.pixelSize: 11
                                    }
                                    Rectangle {
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.bottom: parent.bottom
                                        anchors.bottomMargin: 1
                                        anchors.topMargin: 1
                                        width: 1
                                        gradient: Gradient {
                                            GradientStop { position: 0.0; color: "white" }
                                            GradientStop { position: 1.0; color: "#eee" }
                                        }
                                    }
                                }
                            }
                        }
                    }
                } // tabHookMatrix
                Tab {
                    id: tabCutterStation
                    title: qsTr("CutterStation");
                    active: true
                    anchors.fill: parent
                    Item {
                        property alias lblDopRecordedBy: lblDopRecordedBy;
                        ColumnLayout {
                            id: clCutterStation
                            anchors.fill: parent
                            spacing: 20
                            RowLayout {
                                id: rlRecordedBy
                                anchors.left: parent.left
                                anchors.leftMargin: 20
                                anchors.top: parent.top
                                anchors.topMargin: 10
                                Layout.preferredHeight: 120
                                spacing: 20
                                Label { text: qsTr("Recorded By:"); font.pixelSize: 14; }
                                Label {
                                    id: lblDopRecordedBy;
                                    text: ""
                                    font.pixelSize: 14;
                                }
                            }
                            TableView {
                                id: tvCutterStation
                                headerVisible: true
                                Layout.preferredWidth: parent.width
                                Layout.preferredHeight: 800
//                                anchors.fill: parent
                                verticalScrollBarPolicy: Qt.ScrollBarAsNeeded
//                                verticalScrollBarPolicy: Qt.ScrollBarAlwaysOn
                                model: endOfSiteValidation.cutterStationModel
                                TableViewColumn {
                                    role: 'dropNumber'
                                    title: 'Drop Number'
                                    width: 80
//                                    delegate: Text {
//                                        text: styleData.value ? styleData.value : ""
//                                        horizontalAlignment: Text.AlignHCenter
//                                    }
                                } // dropNumber
                                TableViewColumn {
                                    role: 'angler'
                                    title: 'Angler'
                                    width: 60
//                                    delegate: Text {
//                                        text: styleData.value ? styleData.value : ""
//                                        horizontalAlignment: Text.AlignHCenter
//                                    }
                                } // angler
                                TableViewColumn {
                                    role: 'hook'
                                    title: 'Hook'
                                    width: 40
//                                    delegate: Text {
//                                        text: styleData.value ? styleData.value : ""
//                                        horizontalAlignment: Text.AlignHCenter
//                                    }
                                } // hook
                                TableViewColumn {
                                    role: 'species'
                                    title: 'Species'
                                    width: 120
                                } // species
                                TableViewColumn {
                                    role: 'length'
                                    title: 'Length'
                                    width: 60
                                } // length
                                TableViewColumn {
                                    role: 'weight'
                                    title: 'Weight'
                                    width: 60
                                } // weight
                                TableViewColumn {
                                    role: 'sex'
                                    title: 'Sex'
                                    width: 40
                                } // sex
                                TableViewColumn {
                                    role: 'finclip'
                                    title: 'Finclip'
                                    width: 100
                                } // finclip
                                TableViewColumn {
                                    role: 'otolith'
                                    title: 'Otolith'
                                    width: 80
                                } // otolith
                                TableViewColumn {
                                    role: 'disposition'
                                    title: 'Disposition'
                                    width: 80
                                } // disposition
                                TableViewColumn {
                                    role: 'tagNumber'
                                    title: 'Tag Number'
                                    width: 80
                                } // tagNumber
                                style: TableViewStyle {
                                    itemDelegate: Rectangle {
                                        color: {
                                            (styleData.value && styleData.value != "") ? (styleData.row % 2 ? "white" : "whitesmoke") : "pink";
                                        }
                                        Text {
                                            text: (styleData.value && styleData.value != "") ? styleData.value : ""
                                            horizontalAlignment: Text.AlignHCenter
    //                                        elide: Text.ElideRight
                                            renderType: Text.NativeRendering
                                        }
                                    }
                                }
                            }
                        }
                    }
                } // tabCutterStation
            }
        }
    }
}