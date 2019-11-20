import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0
import QtQuick.Controls.Styles 1.2

import "../common"

Dialog {
    id: dlg
    width: 1060
    height: 600
    title: "Adjust Tow Performance"
    property string accepted_action: ""
    property alias btnOkay: btnOkay
    property alias btnCancel: btnCancel
    property alias swTowPerformance: swTowPerformance
    property alias swMinimumTimeMet: swMinimumTimeMet
    property variant originalTowPerformanceStatus: null
    property variant originalMinimumTimeMetStatus: null

    Connections {
        target: timeSeries.selectedImpactFactorsModel
        onFactorAdded: factorAdded(item);
    }
    function factorAdded(item) {
        var index = timeSeries.availableImpactFactorsModel.get_item_index("factor_lu_id", item["factor_lu_id"]);
//        console.info('removing index from available items: ' + index);
        timeSeries.availableImpactFactorsModel.removeItem(index);
    }

    function addFactors() {

        var idx = [];
        var reverseIdx = [];
        var item;
        tvAvailableReasons.selection.forEach( function(rowIndex) {
            if (rowIndex != -1) idx.push(rowIndex);
        })

        reverseIdx = idx.slice();
        reverseIdx.sort(function(a, b) {return b-a});

        // Remove from available model + add to the selected model
        for (var i = 0; i < reverseIdx.length; i++) {
            item = tvAvailableReasons.model.get(reverseIdx[i]);
            tvAvailableReasons.model.removeItem(reverseIdx[i]);
            tvSelectedReasons.model.append(item);
        }
    }

    function removeFactors() {
        var idx = [];
        tvSelectedReasons.selection.forEach( function(rowIndex) {
            if (rowIndex != -1) idx.push(rowIndex);
        });

        var reverseIdx = [];
        reverseIdx = idx.slice();
        reverseIdx.sort(function(a, b) {return b-a});

        // Remove from selected model + add to the available model
        var item;
        for (var i = 0; i < reverseIdx.length; i++) {
            item = tvSelectedReasons.model.get(reverseIdx[i]);
            tvSelectedReasons.model.removeItem(reverseIdx[i]);
            tvAvailableReasons.model.append(item);
        }
        tvAvailableReasons.model.sort();
    }

    onRejected: {  }
    onAccepted: {
//        var status = "No Change";
//        if ((swTowPerformance.checked != originalTowPerformanceStatus) &
//            (swMinimumTimeMet.checked != originalMinimumTimeMetStatus)) {
//            status = "both"
//        } else if (swTowPerformance.checked != originalTowPerformanceStatus) {
//            status = "tow_performance";
//        } else if (swMinimumTimeMet.checked != originalMinimumTimeMetStatus) {
//            status = "minimum_time_met"
//        }
//        if (status != "No Change")
        timeSeries.adjustTowPerformance(status, swTowPerformance.checked, swMinimumTimeMet.checked);
        timeSeries.adjustImpactFactors();
     }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        GridLayout {
            id: glPerformance
            y: 20
            anchors.horizontalCenter: parent.horizontalCenter
            rows: 2
            columns: 3
            rowSpacing: 30
            columnSpacing: 30
            Label { text: qsTr("Tow Performance:"); font.weight: Font.Bold; }
            Label { text: swTowPerformance.checked ? "Satisfactory" : "Unsatisfactory"; Layout.preferredWidth: 80}
            Switch { id: swTowPerformance; checked: true; } // swTowPerformance
            Label { text: qsTr("Minimum Time Met:"); font.weight: Font.Bold; }
            Label { text: swMinimumTimeMet.checked ? "Yes" : "No"; Layout.preferredWidth: 80}
            Switch { id: swMinimumTimeMet; checked: true; } // swMinimumTimeMet
        } // glPerformance
        RowLayout {
            id: glImpactFactors
            anchors.top: glPerformance.bottom
            anchors.topMargin: 30
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 10
            Column {
                id: clAvailableReasons
                Layout.preferredWidth: 550
                Label {
                    text: qsTr("Available Reasons")
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                TableView {
                    id: tvAvailableReasons
                    width: parent.width
                    height: 400
                    model: timeSeries.availableImpactFactorsModel
                    selectionMode: SelectionMode.ExtendedSelection
                    TableViewColumn {
                        role: "factor_group"
                        title: "Group"
                        width: 250
                    } // factor_group
                    TableViewColumn {
                        role: "factor"
                        title: "Factor"
                        width: 300
                    } // factor
                    onDoubleClicked: { addFactors(); }
                    onClicked: {
                        btnAddFactor.enabled = (currentRow != -1) ? true : false
                    }
                } // tvAvailableReasons
            } // clAvailableReasons
            Column {
                id: clActions
                spacing: 10
                Button {
                    id: btnAddFactor
                    text: qsTr(">")
                    width: 30
                    height: 30
                    enabled: false
                    onClicked: { addFactors(); }
                }
                Button {
                    id: btnRemoveFactor
                    text: qsTr("<")
                    width: 30
                    height: 30
                    enabled: false
                    onClicked: { removeFactors(); }
                }
            } // clActions
            Column {
                id: clSelectedReasons
                Layout.preferredWidth: 370
                Label {
                    text: qsTr("Selected Reasons")
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                TableView {
                    id: tvSelectedReasons
                    width: parent.width
                    height: 400
                    model: timeSeries.selectedImpactFactorsModel
                    selectionMode: SelectionMode.ExtendedSelection
                    TableViewColumn {
                        role: "factor"
                        title: "Factor"
                        width: 290
                    } // factor
                    TableViewColumn {
                        role: "is_unsat_factor"
                        title: "Unsat Factor"
                        width: 70
                    } // factor
                    onDoubleClicked: {
//                        removeFactors();

                        // Change the unsat factor
                        if (currentRow != -1) {
                            var item = model.get(currentRow);
                            var value = (item.is_unsat_factor == "Yes") ? "No" : "Yes"
                            model.setProperty(currentRow, "is_unsat_factor", value);
                        }
                    }
                    onClicked: {
                        btnRemoveFactor.enabled = (currentRow != -1) ? true : false
                    }
                } // tvSelectedReasons
            } // clSelectedReasons
        } // glImpactFactors
        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
            Button {
                id: btnOkay
                text: "Okay"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnOkay
            Button {
                id: btnCancel
                text: "Cancel"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.reject() }
            } // btnCancel
        } // rwlButtons

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
