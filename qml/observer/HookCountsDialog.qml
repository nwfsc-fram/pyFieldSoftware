import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "."
import "../common"

Dialog {
    id: dlg
    width: 800
    height: 600
    title: "Hook Count Calculations"


    property bool enable_audio: ObserverSettings.enableAudio
    property string currentRequiredInfo: "";
    property bool isEnteringGearUnits: false
    property int reqHookCounts: appstate.trips.HookCountsModel.RequiredHookCounts
    property double avgHookCount: appstate.trips.HookCountsModel.AvgHookCount

    function resetAll() {

        appstate.trips.HookCountsModel.initTripHookCounts(appstate.currentTripId);
        if (appstate.trips.HookCountsModel.TotalGearUnits === 0) {
            currentRequiredInfo = "Enter total gear units.";
            isEnteringGearUnits = true;
            numPad.reset();
            tfSkates.forceActiveFocus();
        }
    }

    function updateHookCountsLabel() {
        if(isEnteringGearUnits) {
            currentRequiredInfo = "Enter total gear units.";
        } else if (reqHookCounts >= 1) {
            currentRequiredInfo = "Enter hook counts.";
        } else {
            currentRequiredInfo = "Done. Enter extra\nhook counts if desired.";
        }
    }

    onRejected: {
        console.info("Rejected Hook Counts, but accept anyway");
        dlg.accept();
        //clear();
    }
    onAccepted: {
        if (avgHookCount === 0)
            avgHookCount = 1;
        console.info("Accepted Hook Counts " + avgHookCount);

    }

    onVisibleChanged: {
        // unclear why this is getting called twice with visible === true
        if (visible) {
            resetAll();
        }
    }

    contentItem: RowLayout {
            anchors.fill: parent
            Layout.alignment: Qt.AlignTop
            anchors.margins: 20
            ColumnLayout {
                id: leftCol
                anchors.top: parent.top


                RowLayout {
                    FramLabelHighlightCapable {
                        id: lblTotalSkates
                        text: "Total # of Gear Units"
                        font.pixelSize: 18
                        Layout.preferredWidth: 200
                        state: tfSkates.length > 0 ? "default" : "highlighted"
                        enabled: true
                    }
                    TextField {
                        id: tfSkates
                        font.pixelSize: 18
                        Layout.preferredWidth: 100
                        placeholderText: "# Units"
                        text: appstate.trips.HookCountsModel.TotalGearUnits
                        enabled: true
                        onFocusChanged: {
                            if (focus) {
                                isEnteringGearUnits = true;
                                numPad.attachresult_tf(tfSkates);
                                numPad.setnumpadhint("Total Units");
                                numPad.setnumpadvalue(text);
                                numPad.selectAll();
                                numPad.forceActiveFocus();
                                updateHookCountsLabel();
                            }

                        }
                        onTextChanged: {
                            if (text != "") {
                                console.log(text);
                                var totalSkateCount = parseInt(text);
                                appstate.trips.HookCountsModel.TotalGearUnits = totalSkateCount
                                updateHookCountsLabel();
                                numPad.reset();
                                numPad.setnumpadhint("Hook Count");
                                numPad.setnumpadvalue("");
                                isEnteringGearUnits = false;
                                updateHookCountsLabel();
                            }
                        }
                    }
                }

                ObserverTableView {
                    id: skateHooksTable
                    Layout.preferredWidth: 350
                    Layout.fillHeight: true
                    verticalScrollBarPolicy: Qt.ScrollBarAsNeeded
                    selectionMode: SelectionMode.NoSelection
                    TableViewColumn {
                        role: "index"
                        title: "#"
                        width: 80
                        horizontalAlignment: Text.AlignHCenter
                        delegate: Text {
                            text: model ? skateHooksTable.rowCount - model.index : ""
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.pixelSize: 18
                        }
                    }
                    TableViewColumn {
                        role: "hook_count"
                        title: "Hooks"
                        width: 80
                    }
                    model: appstate.trips.HookCountsModel

                }
                FramButton {
                    text: "Delete top entry"
                    fontsize: 18
                    visible: appstate.trips.HookCountsModel.count > 0
                    onClicked: {
                        // TODO
                        appstate.trips.HookCountsModel.deleteNewest();
                        updateHookCountsLabel();
                    }
                }

                RowLayout {
                    id: hookRow
                    Layout.alignment: Qt.AlignLeft || Qt.AlignTop

                    Label {
                        text: "Average\nHook\nCount"
                        font.pixelSize: 20
                        Layout.preferredWidth: 100
                    }
                    TextField {
                        id: tfAvgHookCount
                        font.pixelSize: 20
                        Layout.preferredWidth: 100
                        text: avgHookCount ? avgHookCount.toFixed(2) : ""
                        readOnly: true
                        enabled: false
                    }
                    ColumnLayout {

                        FramLabel {
                            text: "WARNING: Still need\n" + reqHookCounts + " more hook count(s)\nfor 1/5th of gear units."
                            font.pixelSize: 16
                            font.bold: true
                            visible: reqHookCounts > 0

                        }
                        ObserverSunlightButton {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 50
                            text: reqHookCounts > 0 ? "Accept with\nWarning" : (avgHookCount == 0.0 ? "Accept as 1:1" : "Accept Avg.\nHook Count")
                            Layout.rightMargin: 10
                            fontsize: 20
                            highlightColor: reqHookCounts > 0 ? "red" :"lightgreen"
                            visible: appstate.trips.HookCountsModel.count || (avgHookCount == 0.0 && reqHookCounts == 0)

                            onClicked: {
                                dlg.accept();
                            }
                        }

                    }
                }

            }
            ColumnLayout {
                anchors.top: parent.top
                anchors.left: leftCol.right + 20
                Layout.rightMargin: 100
                Layout.leftMargin: 20

                FramLabel {
                    id: labelCurrentInfo
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 75
                    Layout.alignment: Qt.AlignHCenter || Qt.AlignTop
                    Layout.margins: 10
                    font.pixelSize: 22
                    text: currentRequiredInfo
                }

                ObserverNumPad {
                    Layout.alignment: Qt.AlignLeft || Qt.AlignTop
                    Layout.preferredWidth: 350
                    anchors.topMargin: 10
                    anchors.top: labelCurrentInfo.bottom
                    id: numPad
                    max_digits: numPad.max_digits
                    placeholderText: numPad.placeholderText
                    enable_audio: ObserverSettings.enableAudio
                    onNumpadok: {
                        if (!isEnteringGearUnits&& appstate.trips.HookCountsModel.RequiredHookCounts >= 0 && text_result != "0" && text_result != "") {

                            updateHookCountsLabel()

//                            var newElem = {
//                                skateNum: appstate.trips.HookCountsModel.count + 1,
//                                hookNum: parseInt(text_result)
//                            }
                            appstate.trips.HookCountsModel.addHookCount(parseInt(text_result));
                            numPad.setnumpadhint("Hook Count");
                            numPad.setnumpadvalue("");

                        } else if (result_tf && text_result){

                            result_tf.text = parseInt(text_result);
                        }
                    }
                }
            }

    }
    Keys.onEnterPressed: dlg.accept()
    Keys.onReturnPressed: dlg.accept()
    Keys.onEscapePressed: dlg.reject()
    Keys.onBackPressed: dlg.reject() // especially necessary on Android
}
