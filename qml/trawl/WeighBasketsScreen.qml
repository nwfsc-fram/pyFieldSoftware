import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0

import "../common"

Item {

    property string mode: "takeWeight"
    property string currentWeight: "scaleWeight"
    property bool enableFishingMilitary: false

    signal subsamplecountchanged(int count)
    onSubsamplecountchanged: {
        console.info("new count: " + count)
    }

    Component.onCompleted: {
        main.title = qsTr("Field Collector - Trawl Survey - Backdeck - Weight + Count Baskets");
    }

    Component.onDestruction: {
        changeMode("takeWeight")
        btnWeight.checked = true;
        tbdSM.to_process_catch_state()
    }

    Connections {
        target: tvBaskets.selection
        onSelectionChanged: basketsSelectionChanged();
    }
    Connections {
        target: weighBaskets
        onBasketAdded: tvBaskets.scrollToBottom()
    }
    Connections {
        target: weighBaskets
        onBasketAdded: checkSubsampleCount()
    }
    Connections {
        target: weighBaskets
        onSpeciesChanged: toggleFishingMilitaryButtons(taxonomy_id)
    }

    function toggleFishingMilitaryButtons(taxonomy_id) {
        if ((taxonomy_id === null) || (taxonomy_id === "") || (taxonomy_id === undefined)) {
            enableFishingMilitary = true;

//            btnFishingRelated.state = qsTr("enabled")
//            btnMilitaryRelated.state = qsTr("enabled")
        } else {
            enableFishingMilitary = false;
//            btnFishingRelated.state = qsTr("disabled")
//            btnMilitaryRelated.state = qsTr("disabled")
        }
    }

    function checkSubsampleCount() {
        var soundPlayed = false
        if (tfSubsampleFrequency.text) {
            var diff = tvBaskets.model.count - weighBaskets.lastSubsampleBasket
            if (diff >= parseInt(tfSubsampleFrequency.text)) {
                soundPlayer.play_sound("takeSubsample", false)
                soundPlayed = true
                dlgConfirm.show("to take a subsample", "take subsample")
            }
        }
        if (!soundPlayed) {
            soundPlayer.play_sound("takeWeight", false)
        }
    }

    function basketsSelectionChanged() {

        if (tvBaskets.model.count == 0) {
            btnSubsample.state = qsTr("disabled")
            btnEstimatedWeight.state = qsTr("disabled")
            btnFishingRelated.state = qsTr("disabled")
            btnMilitaryRelated.state = qsTr("disabled")
//            btnSwapSpecies.state = qsTr("disabled")
            btnDeleteEntries.state = qsTr("disabled")

        } else if (tvBaskets.model.count > 0) {
            tvBaskets.selection.forEach(
                function(idx) {
                    btnSubsample.state = qsTr("enabled")
                    btnEstimatedWeight.state = qsTr("enabled")
        //            btnSwapSpecies.state = qsTr("enabled")
                    btnDeleteEntries.state = qsTr("enabled")
                    if (enableFishingMilitary) {
                        btnFishingRelated.state = qsTr("enabled")
                        btnMilitaryRelated.state = qsTr("enabled")
                    } else {
                        btnFishingRelated.state = qsTr("disabled")
                        btnMilitaryRelated.state = qsTr("disabled")
                    }
                }
            )
        }
    }

    function changeMode(newMode) {
        if (newMode == "subsampleFrequency") {
            egMeasurementType.current = null;
            egModifyGroup.current = null;
            numPad.state = qsTr("counts")

        } else if (newMode == "takeWeight") {
            btnWeight.checked = true;
//            if (weighBaskets.weightType == "scaleWeight")
//                btnScaleWeight.checked = true;
//            else
//                btnManualWeight.checked = true;
            numPad.state = qsTr("weights")
            egModifyGroup.current = null;

        } else if (newMode == "modifyWeight") {
            btnWeight.checked = true;
//            if (weighBaskets.weightType == "scaleWeight")
//                btnScaleWeight.checked = true;
//            else
//                btnManualWeight.checked = true;
            numPad.state = qsTr("weights")

        } else if (newMode == "takeCount") {
            btnCount.checked = true;
            egModifyGroup.current = null;
            numPad.state = qsTr("counts")

        } else if (newMode == "modifyCount") {
            btnCount.checked = true;
            numPad.state = qsTr("counts")
        }
//        mode = newMode;
        weighBaskets.mode = newMode
    }

    function processNumPadEntry(value) {

        if (weighBaskets.mode == "takeWeight") {
//            if (weighBaskets.weightType == "scaleWeight") {
//                return;
//            } else if (weighBaskets.weightType == "manualWeight") {
            weighBaskets.add_list_item(value)
            tvBaskets.selection.clear()
            tvBaskets.currentRow = tvBaskets.model.count-1
            tvBaskets.selection.select(tvBaskets.currentRow)
            changeMode("takeCount")
//            }

        } else if (weighBaskets.mode == "modifyWeight") {
            tvBaskets.selection.forEach(
                function(idx) {
                    weighBaskets.update_list_item(idx, "weight", value)
                }
            )
            changeMode("takeWeight")

        } else if (weighBaskets.mode == "subsampleFrequency") {

            if ((value == 0) || (value == null))
                value = ""
            tfSubsampleFrequency.text = value
            changeMode("takeWeight")
            tvBaskets.forceActiveFocus()

        } else if (weighBaskets.mode == "takeCount") {
            tvBaskets.selection.forEach(
                function(idx) {
                    var count = tvBaskets.model.get(idx)["count"]
                    if ((count == "") || (count == null))
                        weighBaskets.update_list_item(idx, "count", value)
                }
            )
            changeMode("takeWeight")

        } else if (weighBaskets.mode == "modifyCount") {
            tvBaskets.selection.forEach(
                function(idx) {
                    weighBaskets.update_list_item(idx, "count", value)
                }
            )
            changeMode("takeWeight")

        }

        numPad.clearnumpad()

    }

    RowLayout {
        id: rwlHeader
        x: 20
        y: 20
        spacing: 10
        Label {
            id: lblSpecies
            text: qsTr("Species")
            font.pixelSize: 20
            Layout.preferredWidth: 80
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfSpecies
            text: stateMachine.species["display_name"]
            font.pixelSize: 20
            Layout.preferredWidth: 300
        }
        Label {
            id: lblProtocol
            text: qsTr("Protocol")
            font.pixelSize: 20
            Layout.preferredWidth: 80
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfProtocol
            text: stateMachine.species["protocol"] ? (
                stateMachine.species["protocol"]["displayName"] ? stateMachine.species["protocol"]["displayName"] : "") : ""
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 300
        }
    } // rwlHeader

    GroupBox {
        id: grpMeasurementType
        x: rwlHeader.x
        y: rwlHeader.y + rwlHeader.height + 40
        width: rwMeasurementTypes.width + 2 * rwMeasurementTypes.spacing
        height: 570
        title: qsTr("Weights & Counts")
        ExclusiveGroup {
            id: egMeasurementType
        }
        ColumnLayout {

            x: 10
            y: rwlHeader.y + 10
            spacing: 10
            Row {
                id: rwMeasurementTypes
                spacing: 20
//                Layout.alignment: Qt.AlignHCenter
                Label { width: 30 }
                TrawlBackdeckButton {
                    id: btnWeight
                    text: qsTr("Weight")
                    checked: true
                    checkable: true
                    exclusiveGroup: egMeasurementType
                    onClicked: {
                        changeMode("takeWeight")
                    }
                } // btnWeight
//                TrawlBackdeckButton {
//                    id: btnScaleWeight
//                    text: qsTr("Scale\nWeight")
//                    checked: true
//                    checkable: true
//                    exclusiveGroup: egMeasurementType
//                    onClicked: {
//                        weighBaskets.weightType = "scaleWeight"
//                        changeMode("takeWeight")
//                    }
//                } // btnScaleWeight
//                TrawlBackdeckButton {
//                    id: btnManualWeight
//                    text: qsTr("Manual\nWeight")
//                    checkable: true
//                    exclusiveGroup: egMeasurementType
//                    onClicked: {
//                        weighBaskets.weightType = "manualWeight"
//                        changeMode("takeWeight")
//                    }
//                } // btnManualWeight
                TrawlBackdeckButton {
                    id: btnCount
                    text: qsTr("Count")
                    checkable: true
                    exclusiveGroup: egMeasurementType
                    onClicked: {
                        changeMode("takeCount")
                    }
                }
                Label { width: 30 }
            } // btnCount
            FramNumPad {
                id: numPad
                x: 175
//                anchors.horizontalCenter: grpMeasurementType.horizontalCenter
                y: 300
//                anchors.top: rwMeasurementTypes.bottom
                state: qsTr("weights")
                onNumpadok: {
                    if (this.stored_result)
                        var numPadValue = this.stored_result
                        if ((weighBaskets.mode == "takeWeight") ||
                            (weighBaskets.mode == "modifyWeight")) {
                            numPadValue = numPadValue ? parseFloat(numPadValue) : null
                        } else if ((weighBaskets.mode == "takeCount") ||
                            (weighBaskets.mode == "modifyCount")) {
                            numPadValue = numPadValue ? parseInt(numPadValue) : null
                        }
                        processNumPadEntry(numPadValue)
                    }
                }
        }
        style: Style {
            property Component panel: Rectangle {
                color: "transparent"
                border.width: 1
//                border.color: "#dddddd"
                Rectangle {
                    height: txtObj.height + 10
                    width: txtObj.width + 10
                    x: txtObj.x - 5
                    y: txtObj.y - 5
                    color: SystemPaletteSingleton.window(true)
                }
                Text {
                    id: txtObj
                    anchors.verticalCenter: parent.top
                    x: 10
                    text: control.title
                    font.pixelSize: 20
                }
            }
        }
    } // grpMeasurementType

    TrawlBackdeckTableView {
        id: tvBaskets
        x: grpMeasurementType.x + grpMeasurementType.width + 20
        y: grpMeasurementType.y
        width: 400
        height: main.height - rwlHeader.height - rllFinishButtons.height - 160
//        selectionMode: SelectionMode.ExtendedSelection
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        verticalScrollBarPolicy: Qt.ScrollBarAsNeeded

//        model: BasketsModel {}
        model: weighBaskets.model

        function scrollToBottom() {
            if (model.count > 0) {
                positionViewAtRow(model.count-1, ListView.Contain)
                currentRow = model.count-1
                selection.clear()
                selection.select(currentRow)
            }
        }

        TableViewColumn {
            role: "basketNumber"
            title: "Bsk"
            width: 50
            delegate: Text {
                text: styleData.value ? styleData.value : ""  //styleData.value.toFixed(3)
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        } // basketNumber
        TableViewColumn {
            role: "weight"
            title: "Kg"
            width: 70
            delegate: Text {
                text: styleData.value ? styleData.value.toFixed(3) : ""  //styleData.value.toFixed(3)
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // weight
        TableViewColumn {
            role: "count"
            title: "Cnt"
            width: 50
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        } // count
        TableViewColumn {
            role: "subsample"
            title: "Sub"
            width: 60
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        } // subsample
        TableViewColumn {
            role: "isWeightEstimated"
            title: "Est"
            width: 60
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        } // isWeightEstimated
        TableViewColumn {
            role: "isFishingRelated"
            title: "Fish"
            width: 60
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        } // isFishingRelated
        TableViewColumn {
            role: "isMilitaryRelated"
            title: "Mil"
            width: 60
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        } // isMilitaryRelated

    } // tvBaskets

    Row {
        ExclusiveGroup {
            id: egModifyGroup
        }
        anchors.left: tvBaskets.left
        y: tvBaskets.y + tvBaskets.height + 10
        spacing: 10
        TrawlBackdeckButton {
            id: btnModifyWeight
            text: qsTr("Modify\nWeight")
            checkable: true
            exclusiveGroup: egModifyGroup
            onClicked: {
                tvBaskets.selection.forEach(
                    function(idx) {
                        numPad.textNumPad.text = tvBaskets.model.get(idx)["weight"] ?
                            tvBaskets.model.get(idx)["weight"].toFixed(3) : ""
                        numPad.textNumPad.selectAll()
                    }
                )
//                modechanged("modifyWeight")
                changeMode("modifyWeight")
            }
        } // btnModifyWeight
        TrawlBackdeckButton {
            id: btnModifyCount
            text: qsTr("Modify\nCount")
            checkable: true
            exclusiveGroup: egModifyGroup
            onClicked: {
                tvBaskets.selection.forEach(
                    function(idx) {
                        var count = tvBaskets.model.get(idx)["count"]
                        if (count != null) {
                            numPad.textNumPad.text = count
                            numPad.textNumPad.selectAll()

                        } else {
                            numPad.textNumPad.text = ""
                        }
                    }
                )

//                modechanged("modifyCount")
                changeMode("modifyCount")

            }
        } // btnModifyCount
        TrawlBackdeckButton {
            id: btnDeleteEntries
            text: qsTr("Delete\nBasket")
            state: qsTr("disabled")
            onClicked: {
                tvBaskets.selection.forEach(
                    function(idx) {
                        dlgConfirm.show("delete this basket", "delete basket")
                    }
                )
            }
        } // btnDeleteEntries
    } // modify buttons
    ColumnLayout {
        id: clStatistics
        x: tvBaskets.x + tvBaskets.width + 10
        y: tvBaskets.y
        width: 100
        spacing: 20

        TrawlBackdeckButton {
            id: btnSubsample
            text: qsTr("Subsample")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
//            checkable: true
            state: qsTr("disabled")
            onClicked: {
                tvBaskets.selection.forEach(
                    function(idx) {
                        if (tvBaskets.model.get(idx)["subsample"] == "Yes") {
                            weighBaskets.update_list_item(idx, "subsample", null)
                        } else {
                            weighBaskets.update_list_item(idx, "subsample", "Yes")
                        }
                    }
                )
            }
        }  // btnSubsample
        Row {
            spacing: 5
            Label {
                id: lblEvery
                text: qsTr("Every")
                font.pixelSize: 18
            }
            TextField {
                id: tfSubsampleFrequency
                placeholderText: qsTr("Nth")
                font.pixelSize: 18
                width: 40
                onFocusChanged: {
                    if (this.focus) {
                        this.selectAll()
                        numPad.textNumPad.text = this.text ? parseInt(this.text) : 0
//                        modechanged("subsampleFrequency")
                        changeMode("subsampleFrequency")

                    }
                }
            }
            Label {
                id: lblBasket
                text: qsTr("basket")
                font.pixelSize: 18
            }
        } // subsample frequency
        Column {
            Label {
                id: lblSubsampleCount
                text: qsTr("Subsample Count")
                font.pixelSize: 18
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfSubsampleCount
                text: weighBaskets.subsampleCount
                font.pixelSize: 18
                readOnly: true
                Layout.preferredWidth: 120
            }
        } // subsample count
        Column {
            Label {
                id: lblNumBaskets
                text: qsTr("Number of Baskets")
                font.pixelSize: 18
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfNumBaskets
                text: weighBaskets.basketCount
                font.pixelSize: 18
                readOnly: true
            }
        } // number of baskets
        Column {
            Label {
                id: lblTotalWeight
                text: qsTr("Total Weight")
                font.pixelSize: 18
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfTotalWeight
//                text: weighBaskets.totalWeight
                text: weighBaskets.totalWeight ? parseFloat(weighBaskets.totalWeight).toFixed(1) : 0
//                text: (typeof weightBaskets.totalWeight == 'number') ? parseFloat(weighBaskets.totalWeight).toFixed(1) : ""
                font.pixelSize: 18
                readOnly: true
            }
        } // total weight
        TrawlBackdeckButton {
            id: btnEstimatedWeight
            text: qsTr("Estimated\nWeight")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            state: qsTr("disabled")
            onClicked: {
                var field = "isWeightEstimated";
                tvBaskets.selection.forEach(
                    function(idx) {
                        if (tvBaskets.model.get(idx)[field] == "Yes") {
                            weighBaskets.update_list_item(idx, field, null)
                        } else {
                            weighBaskets.update_list_item(idx, field, "Yes")
                        }
                    }
                )
            }
        } // btnEstimatedWeight
        TrawlBackdeckButton {
            id: btnFishingRelated
            text: qsTr("Fishing\nRelated")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            state: qsTr("disabled")
            onClicked: {
                var field = "isFishingRelated";
                tvBaskets.selection.forEach(
                    function(idx) {
                        if (tvBaskets.model.get(idx)[field] == "Yes") {
                            weighBaskets.update_list_item(idx, field, null)
                        } else {
                            weighBaskets.update_list_item(idx, field, "Yes")
                        }
                    }
                )
            }
        } // btnFishingRelated
        TrawlBackdeckButton {
            id: btnMilitaryRelated
            text: qsTr("Military\nRelated")
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            state: qsTr("disabled")
            onClicked: {
                var field = "isMilitaryRelated";
                tvBaskets.selection.forEach(
                    function(idx) {
                        if (tvBaskets.model.get(idx)[field] == "Yes") {
                            weighBaskets.update_list_item(idx, field, null)
                        } else {
                            weighBaskets.update_list_item(idx, field, "Yes")
                        }
                    }
                )
            }
        } // btnMilitaryRelated

//        TrawlBackdeckButton {
//            id: btnSwapSpecies
//            text: qsTr("Swap\nSpecies")
//            Layout.preferredWidth: 120
//            Layout.preferredHeight: 60
//            state: qsTr("disabled")
//        } // btnSwapSpecies

    } // clStatistics
    RowLayout {
        id: rllFinishButtons
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        spacing: 10

        TrawlBackdeckButton {
            id: btnNotes
            text: qsTr("Note")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: {
                dlgNote.reset(tvBaskets)
                dlgNote.open()
                return;
                var results = notes.getNote(dlgNote.primaryKey)
            }
        }
        TrawlBackdeckButton {
            id: btnBack
            text: qsTr("<<")
            x: main.width - this.width - 20
            y: main.height - this.height - 20
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: screens.pop()
        }
    } // rllFinishButtons

    TrawlNoteDialog { id: dlgNote }

    FramConfirmDialog {
        id: dlgConfirm
        visible: false
        action_label: "remove the species\nit has data associated with it"
        auto_hide: true

        onCancelledFunc: {
            this.hide()
        }

        onConfirmedFunc: {
            if (action_name == "delete basket") {
                tvBaskets.selection.forEach(
                    function(idx) {
                        weighBaskets.delete_list_item(idx)
                        tvBaskets.selection.clear()
                        if (tvBaskets.model.count > 0) {
                            if (idx == 0) {
                                tvBaskets.currentRow = 0
                            } else if ((idx > 0) & (idx-1 < tvBaskets.model.count)) {
                                tvBaskets.currentRow = idx - 1
                            }
                            tvBaskets.selection.select(tvBaskets.currentRow)
                        }
                    }
                )
            } else if (action_name == "take subsample") {
                tvBaskets.selection.forEach(
                    function(idx) {
                        weighBaskets.update_list_item(idx, "subsample", "Yes")
                        weighBaskets.lastSubsampleBasket = idx + 1
                    }
                )
            }
        }
    } // FramConfirmDialog

}