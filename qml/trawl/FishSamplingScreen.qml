import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Window 2.2

import "../common"

Item {
    id: root

    property string sex: "female"
    property string linealType: "length"
//    property real linealValue
//    property real weight
//    property int age
    property var linealValue
    property var weight
    property var age
    property string ageTypeName
    property int ovaryNumber
    property int stomachNumber
    property int tissueNumber
    property int finclipNumber
    property var protocols: {"sex": null, "linealValue": null, "age": null, "weight": null,
                            "ovary": null, "stomach": null, "tissue": null, "finclip": null}

    property var current_numpad_value;

    property alias btnPrinter1: btnPrinter1

    Component.onCompleted: {

        btnMode.checked = (fishSampling.mode == 'Age-Weight') ? true : false

        selectSpecimen();
        selectTab();
        setProtocolInformation();
        fishSampling.sex = "F"      // Reset sex to Female on page entry

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
        tbdSM.to_process_catch_state()
    }

    Connections {
        target: tvSpecimens.selection
        onSelectionChanged: specimenSelected();
    } // onSelectionChanged
    Connections {
        target: tabWeightAge.item.cbSampleType
        onCurrentIndexChanged: changeAgeType();
    } // onCurrentIndexChanged
    Connections {
        target: tabOvStTiFc.item.tvSamples.selection
        onSelectionChanged: changeSpecialRow();
    } // onSelectionChanged
    Connections {
        target: fishSampling
        onSpecimenAdded: selectLastSpecimen();
    } // onSpecimenAdded

    // Tab Changes
    Connections {
        target: tvActions
        onCurrentIndexChanged: tabSelectionChanged();
    } // onCurrentIndexChanged
    Connections {
        target: fishSampling
        onTabChanged: selectTab();
    } // onTabChanged

    Connections {
        target: fishSampling
        onActionModeChanged: changeActionMode();
    } // fishhSampling.onActionModeChanged
    Connections {
        target: fishSampling
        onValueChanged: updateTabValues(tabIndex, property);
    } // fishSampling.onValueChanged
    Connections {
        target: fishSampling
        onInvalidEntryReceived: processInvalidEntry(add_or_update, property, value, errors);
    }
    Connections {
        target: fishSampling
        onPrinterStatusReceived: processPrinterStatus(comport, success, message)
    }
    Connections {
        target: fishSampling
        onModeChanged: modeChanged()
    }

    function modeChanged() {
        switch (fishSampling.mode) {
            case "Sex-Length":
                btnMode.checked = false
                tabWeightAge.state = qsTr("disabled")
                tabOvStTiFc.state = qsTr("disabled")
                tvActions.currentIndex = 0
                break;
            case "Age-Weight":
                btnMode.checked = true
                if ((tvSpecimens.currentRow != -1) && (tvSpecimens.model.count > 0)) {
                    tabWeightAge.state = qsTr("enabled")
                    tabOvStTiFc.state = qsTr("enabled")
                } else {
                    tabWeightAge.state = qsTr("disabled")
                    tabOvStTiFc.state = qsTr("disabled")
                }
                break;
        }
    }

    function changeSpecialRow() {
        var model = tabOvStTiFc.item.tvSamples.model;
        var currentRow = tabOvStTiFc.item.tvSamples.currentRow;
        if (currentRow != -1) {
            var value = model.get(currentRow).value;
            var type = model.get(currentRow).type

//            tabOvStTiFc.item.btnReviewTags.state = qsTr("enabled")

            // Update the number pad appropriately.  If we have -'s in the number, blank out the number pad
            if (value == null)
                numPad.textNumPad.text = ""
            else {
                if (value.toString().indexOf('-') === -1) {
                    numPad.textNumPad.text = value
                } else
                    numPad.textNumPad.text = ""
            }

            if ((type == "ovaryNumber") || (type == "stomachNumber") || (type == "tissueNumber")) {
                tabOvStTiFc.item.btnAssignTagId.state = qsTr("enabled")

                if ((value != "") && (value != null))
                    btnPrintLabel.state = qsTr("enabled")
                else
                    btnPrintLabel.state = qsTr("disabled")

            } else {
                tabOvStTiFc.item.btnAssignTagId.state = qsTr("disabled")
                btnPrintLabel.state = qsTr("disabled")
            }
        }
    }

    function processPrinterStatus(comport, success, message) {
        if (!success) {
            msg.show(comport + " printing error: " + message)

        }
    }

    function processInvalidEntry(add_or_update, property, value, errors) {
        var dlg;
        switch (property) {
            case "ageNumber":
                dlg = dlgAge
                break;
            case "weight":
                dlg = dlgWeight
                break;

            case "linealValue":
                if (add_or_update == "add") {
                    dlg = dlgLinealAdd
                } else if (add_or_update == "update") {
                    dlg = dlgLinealUpdate
                } else {
                    return;
                }
                break;

            case "sex":
                dlg = dlgSex
                break;
        }
//        console.info('value: ' + value)
//        dlg.value = value
        dlg.setvalue(value)
        dlg.errors = errors
        dlg.open()

        return;


        if (property == "ageNumber") {
            // Needed when coming from the barcode reader
//            tabWeightAge.item.tfAge.text = value ? value : "";
            dlgConfirm.show(errors, "barcode errors")

        } else if (property == "weight") {
//            tabWeightAge.item.tfWeight.text = value ? value : "";
            dlgConfirm.show(errors, "weight error")

        } else if (property == "linealValue") {
            tabSexLength.item.tfLineal.text = value ? value : "";
            dlgLineal.value = value
            dlgLineal.errors = errors
            dlgLineal.open()

//            dlgConfirm.show(errors, "linealValue error")

        } else if (property == "sex") {
            dlgConfirm.show(errors, "sex error")
        }
    }

    function overrideBarcode() {
        dlgConfirm.show("to override the age", "override barcode")
    }

    function changeActionMode() {
        btnModifyEntry.checked = (fishSampling.actionMode == "add") ? false : true
    }

    function toTitleCase(str) {
        return str.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
    }

    function setProtocolInformation() {
        var protocol = stateMachine.species["protocol"]
        var title = "Length";
        var linealType = ""
        var actions = protocol["actions"]

//        console.info('species: ' + stateMachine.species["display_name"])
//        console.info('setProtocolInfo, len: ' + actions.length + ', actions: ' + JSON.stringify(actions))

//        if ((actions != null) && (actions != "")) {
        if (actions.length > 0) {
            var types = actions.map(function(action){ return action.type.toLowerCase(); });
//            console.info('types: ' + types)
            var counts = actions.map(function(action) { return action.count; });
            var hasLength = ["length"].some(function(type){ return types.indexOf(type) != -1; });
            title = hasLength ? "Length" : "Width"
            var elem = actions.filter(function(item) { return item.type === title; });
            var linealType = elem[0]["subType"]
        }
        tabSexLength.title = "Sex &\n" + title
        tabSexLength.item.lblLineal.text = linealType ? linealType + " " + title : title
        fishSampling.linealType = linealType ? linealType + " " + title : title
//        console.info(fishSampling.linealType)
    }

    function selectTab() {

        switch (fishSampling.activeTab) {
            case "Sex-Length":
                tvActions.currentIndex = 0
                break;
            case "Age-Weight":
                tvActions.currentIndex = 1
                break;
            case "Ovary-Stomach":
                tvActions.currentIndex = 2
                break;
        }
    }

    function updateTabValues(tabIndex, property) {

        if (tvSpecimens.currentRow == -1) return;

        var item = tvSpecimens.model.get(tvSpecimens.currentRow)
        var tab = tvActions.getTab(tabIndex)
        switch (tab) {
            case tabSexLength:
                sex = item["sex"] ? item["sex"] : "F"
                if (sex == "F")
                    tab.item.btnFemale.checked = true;
                else if (sex == "M")
                    tab.item.btnMale.checked = true;
                else if (sex == "U")
                    tab.item.btnUnsex.checked = true;
                linealType = item["linealType"] ? item["linealType"] : linealType
                linealValue = (typeof item["linealValue"] == 'number') ? item["linealValue"] : ""
                tab.item.tfLineal.text = (typeof linealValue == 'number') ? parseFloat(linealValue).toFixed(1) : ""

                if (tvActions.currentIndex == tabIndex) {
                    // Select all of the text of the numPad
                    numPad.textNumPad.text = tab.item.tfLineal.text
                    tab.item.tfLineal.forceActiveFocus()
                    tab.item.tfLineal.selectAll()
//                    numPad.textNumPad.forceActiveFocus()
                    numPad.textNumPad.selectAll()
                }

                break;

            case tabWeightAge:

                current_numpad_value = numPad.textNumPad.text

                weight = (typeof item["weight"] == 'number') ? item["weight"] : ""
                age = (typeof item["ageNumber"] == 'number') ? item["ageNumber"] : ""
                ageTypeName = item["ageTypeName"] ? item["ageTypeName"] : "Otolith"
                tab.item.tfWeight.text = (typeof weight == 'number') ? parseFloat(weight).toFixed(3) : ""
                tab.item.tfAge.text = (typeof age == 'number') ? age.toString() : ""
                tab.item.cbSampleType.currentIndex = tab.item.cbSampleType.find(ageTypeName.toString())

                if (tvActions.currentIndex == tabIndex) {

                    // Always set focus on the tfWeight textfield
                    tab.item.tfWeight.forceActiveFocus()

                    // TEST to fix overwriting manual weight entry in the numpad
//                    numPad.textNumPad.text = current_numpad_value;
//                    numPad.textNumPad.selectAll()



//                    console.info('updateTabValues, numPad value: ' + current_numpad_value);


                    // Select all of the text tfAge and then numPad
//                    if (tab.item.tfWeight.activeFocus) {
//                        numPad.textNumPad.text = tab.item.tfAge.text
//                        tab.item.tfAge.selectAll()
//                        tab.item.tfAge.forceActiveFocus()
//                        numPad.textNumPad.selectAll()
//                    }


                    // If the auto-update is coming from the barcode reader
//                    if (property == "ageNumber") {
//                    } else {
//                        numPad.textNumPad.text = tab.item.tfWeight.text
//                    }


                }


                break;

            case tabOvStTiFc:
                var tvSamples = tab.item.tvSamples;
                var standardItems = ["ovary", "stomach", "tissue", "finclip"]
                var value;
                for (var i=0; i<standardItems.length; i++) {
                    value = (item[standardItems[i] + "Number"] != null) ? item[standardItems[i] + "Number"] : ""
                    tvSamples.model.setProperty(i, "value", value)
                }

                var row = tvSamples.model.get_item_index("type", property)
                if (row != -1) {
                    tvSamples.currentRow = row;
                    tvSamples.selection.select(tvSamples.currentRow);

                    if (tvActions.currentIndex == tabIndex) {
//                        console.info('os active')
                        if ((tvSamples.model.get(tvSamples.currentRow).value) &&
                            (property == "finclipNumber"))
                            numPad.textNumPad.text = tvSamples.model.get(tvSamples.currentRow).value
                        else
                            numPad.textNumPad.text = ""
                    }
                }

                break;

        }
        if ((item["sex"] != "") & (item["linealValue"] != null)) {
            btnSpecialAction.state = qsTr("enabled")
        } else {
            btnSpecialAction.state = qsTr("disabled")
        }
    }

    function selectLastSpecimen() {
        // Function used to select the last tvSpecimens entry (used when taking in a new length
        // from the fishmeter board, and tied to the fishSampling specimenAdded signal
        tvSpecimens.currentRow = -1
        tvSpecimens.selection.clear()
        tvSpecimens.currentRow = tvSpecimens.model.count-1
        tvSpecimens.selection.select(tvSpecimens.model.count-1)
    }

    function selectSpecimen() {
        tvSpecimens.currentRow = -1
        tvSpecimens.selection.clear()

//        console.info('selectSpecimen, state specimen: ' + stateMachine.specimen["parentSpecimenId"])

        if (stateMachine.specimen["parentSpecimenId"] != null) {
            var parentSpecimenId = stateMachine.specimen["parentSpecimenId"]
            var currentIndex = tvSpecimens.model.get_item_index("parentSpecimenId", parentSpecimenId)
            if (currentIndex != -1) {
                tvSpecimens.currentRow = currentIndex
                tvSpecimens.selection.select(currentIndex)
            } else {
                fishSampling.activeTab = "Sex-Length"
            }
        } else {
            fishSampling.activeTab = "Sex-Length"
        }
    }

    function specimenSelected() {
        var state = qsTr("disabled")

        if (tvSpecimens.model.count > 0) {
            tvSpecimens.selection.forEach (
                function(rowIndex) {
                    state = qsTr("enabled")
                    var item = tvSpecimens.model.get(rowIndex)
                    if (item) {


                        // Update the stateMachine specimen
                        var smItem = {"parentSpecimenId": item["parentSpecimenId"], "row": tvSpecimens.currentRow,
                                        "specimenNumber": item["parentSpecimenNumber"],
                                        "sex": item["sex"], "linealValue": item["linealValue"]}
                        stateMachine.specimen = smItem

                        // Update the values in each of the tvActions tabs
                        for (var i=0; i<tvActions.count; i++) {
                            updateTabValues(i);
                        }

                        // Disable the print label button
                        tvActions.getTab(2).item.tvSamples.selection.clear()
                        tvActions.getTab(2).item.tvSamples.currentRow = -1
                        btnPrintLabel.state = qsTr("disabled")
                        tvActions.getTab(2).item.btnAssignTagId.state = qsTr("disabled")
//                        tvActions.getTab(2).item.btnReviewTags.state = qsTr("disabled")

                    }
                }
            )
        }

        btnModifyEntry.state = state
        btnDeleteEntry.state = state
        if (fishSampling.mode == "Age-Weight") {
            tabWeightAge.state = state
            tabOvStTiFc.state = state
        }
    }

    function tabSelectionChanged() {
        var tab = tvActions.getTab(tvActions.currentIndex)
        switch (tab) {
            case tabSexLength:
                fishSampling.activeTab = "Sex-Length"
                // TODO Todd Hay - why isn't this working for the tabSexLength tab?
//                root.forceActiveFocus()
                tab.item.tfLineal.forceActiveFocus()
                tab.item.tfLineal.selectAll()
                numPad.textNumPad.text = tab.item.tfLineal.text ? parseFloat(tab.item.tfLineal.text).toFixed(1) : ""
//                numPad.textNumPad.forceActiveFocus()
                numPad.textNumPad.selectAll()
                numPad.state = qsTr("weights")
                break;

            case tabWeightAge:
                fishSampling.activeTab = "Age-Weight"
                tab.item.tfWeight.forceActiveFocus()
                tab.item.tfWeight.selectAll()
//                tab.item.tfAge.deselect()
                numPad.state = qsTr("weights")
                numPad.textNumPad.text = tab.item.tfWeight.text ? parseFloat(tab.item.tfWeight.text).toFixed(3) : ""
//                numPad.textNumPad.forceActiveFocus()
                numPad.textNumPad.selectAll()

                break;

            case tabOvStTiFc:
                fishSampling.activeTab = "Ovary-Stomach"
                tab.item.tvSamples.forceActiveFocus()
                break;
        }
    }

    function changeSex(sex) {
        fishSampling.sex = sex
        if (fishSampling.actionMode == "modify") {
            if (tvSpecimens.currentRow != -1) {
                fishSampling.update_list_item("sex", fishSampling.sex)
//                btnModifyEntry.checked = false
            }
        }
    }

    function changeAgeType() {

        var cbSampleType = tabWeightAge.item.cbSampleType;
        fishSampling.ageType = cbSampleType.textAt(cbSampleType.currentIndex)
        if (tvSpecimens.currentRow != -1) {
            fishSampling.update_list_item("ageTypeName", fishSampling.ageType)
        }
    }

    function protocolChecks() {

        screens.pop();
        return;

        // Age-Weight Fish - no age or no weight taken
        var protocols = stateMachine.species["protocol"]["actions"]
        console.info('protocols: ' + protocols)
        if (protocols != "") {
            var types = protocols.map(function(action){ return action.type.toLowerCase(); });
            var isAge = ["age id "].some(function(type){ return types.indexOf(type) != -1; });
            var isWeight = ["weight"].some(function(type) { return types.indexOf(type) != -1; });

            var hasAge = false;
            var hasWeight = false;
            var items = tvSpecimens.model.items;
            for (var i=0; i < items.length; i++) {
                if (items[i]["ageNumber"] != null)
                    hasAge = true;
                if (items[i]["weight"] != null)
                    hasWeight = true;
                if ((hasAge) && (hasWeight))
                    break;
            }
            console.info('hasAge: ' + hasAge + ', hasWeight: ' + hasWeight);
            if ((hasAge == false) || (hasWeight == false))
                dlgConfirm.show("to leave Fish Sampling\nYou are missing Ages or Weights", "leave screen");
            else
                screens.pop()
        } else {
            screens.pop()
        }
    }

    GridLayout {
        id: gdlHeader
        x: 20
        y: 20
        columns: 3
        columnSpacing: 10
        rowSpacing: 10
        Label {
            id: lblSpecies
            text: qsTr("Species")
            font.pixelSize: 20
            Layout.preferredWidth: 70
        } // lblSpecies
        TrawlBackdeckTextFieldDisabled {
            id: tfSpecies
            text: stateMachine.species["display_name"]
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 320
            Layout.columnSpan: 2
        } // tfSpecies
        Label {
            id: lblProtocol
            text: qsTr("Protocol")
            font.pixelSize: 20
            Layout.preferredWidth: 70
        } // lblProtocol
        TrawlBackdeckTextFieldDisabled {
            id: tfProtocol
            text: stateMachine.species["protocol"]["displayName"] ? stateMachine.species["protocol"]["displayName"] : ""
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 220
        } // tfProtocol
        TrawlBackdeckButton {
            id: btnMode
            text: "Mode:\n" + fishSampling.mode
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            checkable: true
            checked: false
            onClicked: { fishSampling.mode = checked ? "Age-Weight" : "Sex-Length" }
        } // btnMode
    } // gdlHeader

    TrawlBackdeckTableView {
        id: tvSpecimens
        x: gdlHeader.x
        y: gdlHeader.y + gdlHeader.height + 10
        width: 430
        height: 520
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        model: fishSampling.model

        TableViewColumn {
            role: "parentSpecimenNumber"
            title: "ID"
            width: 60
        }
         TableViewColumn {
            role: "sex"
            title: "Sex"
            width: 60
        }
       TableViewColumn {
            role: "linealValue"
            title: "Len"
            width: 60
            delegate: Text {
                text: (typeof styleData.value == 'number') ? styleData.value.toFixed(1) : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        }
        TableViewColumn {
            role: "weight"
            title: "Wgt"
            width: 80
            delegate: Text {
                text: (typeof styleData.value == 'number') ? styleData.value.toFixed(3) : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        }
        TableViewColumn {
            role: "ageNumber"
            title: "Age"
            width: 120
            delegate: Text {
                text: (typeof styleData.value == 'number') ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        }
        TableViewColumn {
            role: "special"
            title: "Sp"
            width: 50
        }
    } // tvSpecimens

    RowLayout {
        id: rwlEntryButtons
        anchors.left: tvSpecimens.left
        y: tvSpecimens.y + tvSpecimens.height + 10
        spacing: 10
        TrawlBackdeckButton {
            id: btnAddEntry
            text: qsTr("Add\nEntry")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            onClicked: {
                var tab = tvActions.getTab(tvActions.currentIndex)
                if (tab == tabSexLength) {
//                    fishSampling.add_list_item(linealValue, fishSampling.sex)

                    linealValue = null
//                    linealValue = 0
                    numPad.textNumPad.text = linealValue ? linealValue : "";
                    fishSampling.add_list_item(linealValue, fishSampling.sex)
                }
            }
        } // btnAddEntry
        TrawlBackdeckButton {
            id: btnModifyEntry
            text: qsTr("Modify\nEntry")
            state: qsTr("disabled")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            checkable: true
            checked: false
            onClicked: {
                fishSampling.actionMode = checked ? "modify" : "add"
            }
        } // btnModifyEntry
        TrawlBackdeckButton {
            id: btnDeleteEntry
            text: qsTr("Delete\nEntry")
            state: qsTr("disabled")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            onClicked: {
                if (tvSpecimens.currentRow != -1) {
                    fishSampling.playSound("deleteItem")
                    var specNum = tvSpecimens.model.get(tvSpecimens.currentRow)["parentSpecimenNumber"];
                    dlgRemoveSpecies.speciesNumber = specNum;
                    dlgRemoveSpecies.open();
//                dlgConfirm.show("Are you sure you want\nto delete the specimen?", "delete specimen")
                }
            }
        } // btnDeleteEntry
    } // rwlEntryButtons

    TabView {
        id: tvActions
        x: main.width - this.width - 10
        y: gdlHeader.y
        width: 520
        height: 250

        style: TabViewStyle {
            frameOverlap: 1
            tab: Rectangle {
//                color: styleData.selected ? "steelblue" :"lightsteelblue"
                color: styleData.selected ? "lightgray" : SystemPaletteSingleton.window(true)
                border.color:  styleData.selected ? "black" : "lightgray" //"steelblue"
//                border.width: styleData.selected ? 2 : 1
//                implicitWidth: Math.max(text.width + 4, 80)
                implicitWidth: 120
                implicitHeight: 60
                radius: 3
                Text {
                    id: text
                    font.pixelSize: 20
                    anchors.centerIn: parent
                    text: styleData.title
//                    color: styleData.selected ? "white" : "black"
                    color: styleData.enabled ? "black" : "#a8a8a8"
                }
//                MouseArea {
//
//                    onClicked: screens.push(Qt.resolvedUrl("SpecialSamplingScreen.qml"))
//
//                }
            }
//            frame: Rectangle { color: "steelblue" }
            frame: Rectangle {
                border.color: "black"
                color: SystemPaletteSingleton.window(true)
            }

        }

        Tab {
            id: tabSexLength
            title: ""
            active: true
            Item {
                x: 20
                y: 20

                property alias tfLineal: tfLineal
                property alias lblLineal: lblLineal
                property alias btnFemale: btnFemale
                property alias btnMale: btnMale
                property alias btnUnsex: btnUnsex

                RowLayout {
                    id: rwlSex
                    ExclusiveGroup {
                        id: egSexType
                    }

                    Label {
                        id: lblSex
                        text: qsTr("Sex")
                        font.pixelSize: 20
                        Layout.preferredWidth: 70
                    } // lblSex


                    TrawlBackdeckButton {
                        id: btnFemale
                        text: qsTr("Female")
                        checked: true
                        checkable: true
                        exclusiveGroup: egSexType
                        Layout.preferredWidth: this.width
                        Layout.preferredHeight: this.height
                        onClicked: changeSex("F")
                        activeFocusOnTab: false
                    } // btnFemale
                    TrawlBackdeckButton {
                        id: btnMale
                        text: qsTr("Male")
                        checkable: true
                        exclusiveGroup: egSexType
                        Layout.preferredWidth: this.width
                        Layout.preferredHeight: this.height
                        onClicked: changeSex("M")
                        activeFocusOnTab: false
                    } // btnMale
                    TrawlBackdeckButton {
                        id: btnUnsex
                        text: qsTr("Unsex")
                        checkable: true
                        exclusiveGroup: egSexType
                        Layout.preferredWidth: this.width
                        Layout.preferredHeight: this.height
                        onClicked: changeSex("U")
                        activeFocusOnTab: false
                    } // btnUnsex
                }
                RowLayout {
                    id: rwlLineal
                    anchors.top: rwlSex.bottom
                    anchors.topMargin: 20
                    anchors.left: rwlSex.left
                    Label {
                        id: lblLineal
                        text: "Length"
                        font.pixelSize: 20
                        Layout.preferredWidth: 160
                    }
                    TextField {
                        id: tfLineal
                        font.pixelSize: 20
                        Layout.preferredHeight: 40
                        Layout.preferredWidth: 120
                        activeFocusOnTab: true
                        MouseArea {
                            anchors.fill: parent
                            onEntered: {
                                numPad.state = qsTr("weights")
                                parent.forceActiveFocus()
                                parent.selectAll()
                                if (parent.text == "")
                                    numPad.textNumPad.text = ""
                                else if (!isNaN(parent.text))
                                    numPad.textNumPad.text = parseFloat(parent.text).toFixed(1)
                                numPad.textNumPad.selectAll()
                            }
                        }
                    } // tfLineal
                    Label {
                        id: lblCm
                        text: "cm"
                        font.pixelSize: 20
                        Layout.preferredWidth: 30
                    }
                }
            }
        } // tabSexLength
        Tab {
            id: tabWeightAge
            title: "Age &\nWeight"
            active: true
            onVisibleChanged: {
                // Check to ensure that the weight and age are populated when leaving the tab
//                if (tvActions.currentIndex == 1) {
                if ((!this.visible) && (tabSexLength.visible)) {
                    var weight = tabWeightAge.item.tfWeight.text
                    weight = weight ? parseFloat(weight) : null
                    var age = tabWeightAge.item.tfAge.text
                    age = age ? parseInt(age) : null
                    var msg = "";
                    var success = qaqc.fishSamplingLeaveAgeWeightTabCheck(weight, age)
                    if (!success) {
                        dlgOkayCancel.target = "tabSexLength"
                        if ((age == null) && (weight == null))
                            msg = "Your Weight and Age are empty"
                        else if (age == null)
                            msg = "Your Age is empty"
                        else if (weight == null)
                            msg = "Your Weight is empty"
                        dlgOkayCancel.message = msg
                        dlgOkayCancel.open()
                    }
                }
            }
//            state: qsTr("disabled")
            state: fishSampling.mode == "Age-Weight" ? qsTr("enabled") : qsTr("disabled")
            Rectangle { color: SystemPaletteSingleton.window(true) }
            Item {
                x: 20
                y: 20

                property alias tfWeight: tfWeight
                property alias tfAge: tfAge
                property alias cbSampleType: cbSampleType

                RowLayout {
                    id: rwlWeight
                    spacing: 10

                    Label {
                        text: qsTr("Weight")
                        font.pixelSize: 20
                    }
                    TextField {
                        id: tfWeight
                        font.pixelSize: 20
                        Layout.preferredHeight: 40
                        Layout.preferredWidth: 150
                        Layout.columnSpan: 3
                        placeholderText: qsTr("Weight (kg)")
                        activeFocusOnTab: true
                        MouseArea {
                            anchors.fill: parent
                            onEntered: {
                                numPad.state = qsTr("weights")
                                tfAge.deselect()
                                parent.forceActiveFocus()
                                parent.selectAll()

                                console.info('tfWeight entered: ' + current_numpad_value);
                                if (!isNaN(current_numpad_value)) {
                                    numPad.textNumPad.text = current_numpad_value;
                                } else if (parent.text == "") {
                                    numPad.textNumPad.text = "";
                                } else if (!isNaN(parent.text)) {
//                                    numPad.textNumPad.text = Number(parent.text)
                                    numPad.textNumPad.text = parseFloat(parent.text).toFixed(3);
                                }
                                numPad.textNumPad.selectAll()
                            }
                        }
                    } // tfWeight
                } // tfWeight
                RowLayout {
                    id: rwlAge
                    x: rwlWeight.x
                    y: rwlWeight.y + rwlWeight.height + 10
                    spacing: 30
                    Label {
                        text: qsTr("Age")
                        font.pixelSize: 20
                    }
                    TextField {
                        id: tfAge
//                        text: qsTr("100200300")
                        placeholderText:  qsTr("Age Tag ID")
                        font.pixelSize: 20
                        Layout.preferredWidth: 150
                        Layout.preferredHeight: 40
                        MouseArea {
                            anchors.fill: parent
//                            hoverEnabled: true
                            onEntered: {
                                numPad.state = qsTr("counts")
                                tfWeight.deselect()
                                parent.forceActiveFocus()
                                parent.selectAll()

                                console.info('tfAge onEntered: ' + current_numpad_value);
                                if (!isNaN(current_numpad_value)) {
                                    numPad.textNumPad.text = current_numpad_value;
                                } else if (parent.text == "") {
                                    numPad.textNumPad.text = ""
                                } else if (!isNaN(parent.text)) {
                                    numPad.textNumPad.text = Number(parent.text)
                                }
                                numPad.textNumPad.selectAll()
                            }
                        }
                    }
                    ColumnLayout {
//                        spacing: 10
                        Label {
                            text: qsTr("Structure Type")
                            font.pixelSize: 20
                            Layout.preferredWidth: 100
                        }
                        TrawlBackdeckComboBox {
                            id: cbSampleType
                            currentIndex: 0
                            Layout.preferredHeight: 40
                            Layout.preferredWidth: 220
                            model: fishSampling.ageStructuresModel

                        }
                    }
                } // tfAge
            }
            states: [
                State {
                    name: "enabled"
                    PropertyChanges { target: tabWeightAge; enabled: true; }
                },
                State {
                    name: "disabled"
                    PropertyChanges { target: tabWeightAge; enabled: false; }
                }
            ]
        } // tabWeightAge
        Tab {
            id: tabOvStTiFc
            title: "Ovary &\nStomach +"
            active: true

            state: fishSampling.mode == "Age-Weight" ? qsTr("enabled") : qsTr("disabled")
            Rectangle { color: SystemPaletteSingleton.window(true) }
            anchors.margins: 10

            Item {
                property alias tvSamples: tvSamples
                property alias btnAssignTagId: btnAssignTagId
                property alias btnReviewTags: btnReviewTags

                TrawlBackdeckTableView {
                    id: tvSamples
                    width: 370
                    height: 150
                    selectionMode: SelectionMode.SingleSelection
                    headerVisible: true
                    horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
                    model: fishSampling.StandardActionsModel

                    TableViewColumn {
                        role: "text"
                        title: "Sample Type"
                        width: 140
                    }
                    TableViewColumn {
                        role: "value"
                        title: "Tag ID"
                        width: 230
                        delegate: Text {
                            text: (styleData.value != undefined) ? styleData.value : ""
                            font.pixelSize: 20
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                } // tvSamples
                ColumnLayout {
                    id: clAssignTagId
                    anchors.left: tvSamples.right
                    anchors.top: tvSamples.top
                    anchors.leftMargin: 10
                    spacing: 10
                    TrawlBackdeckButton {
                        id: btnAssignTagId
                        text: "Assign\nTag ID"
                        Layout.preferredHeight: this.height
                        Layout.preferredWidth: this.width
                        state: qsTr("disabled")
                        onClicked: {
                            // Assign it to the currently selected tvSamples row
                            if (tvSamples.currentRow != -1) {
                                var item = tvSamples.model.get(tvSamples.currentRow)
                                if (item["type"] === "ovaryNumber") {
                                    if (tvSpecimens.currentRow !== -1) {
                                        var specimenItem = tvSpecimens.model.get(tvSpecimens.currentRow);
                                        var specimenSex = specimenItem.sex;
                                        if (specimenSex === "M") {
                                            dlgOkay.message = "CRITICAL ERROR - DELETING ENTIRE DATABASE...\n\nJust kidding, males can't have ovaries, please try again"
                                            dlgOkay.open()
                                            return;
                                        }
                                    }
                                }

                                var tagId = fishSampling.get_tag_id(item["type"])
                                if (tagId != "") {
                                    fishSampling.update_list_item(item["type"], tagId)
                                    tvSamples.selection.select(tvSamples.currentRow);

                                } else {

                                    // Gosh, problems, we still have a duplicate tag id
                                    dlgOkay.target = "tabOvStTiFc"
                                    var msg = "You have a duplicate tag: " + tagId + "\n\nPlease resort to manual tags"
                                    dlgOkay.message = msg
                                    dlgOkay.open()

                                }
                                numPad.textNumPad.text = ""
                            }
                        }
                    }
                    TrawlBackdeckButton {
                        id: btnReviewTags
                        text: "Review\nTags"
                        Layout.preferredHeight: this.height
                        Layout.preferredWidth: this.width
                        state: qsTr("enabled")
                        onClicked: {
                            dlgSpecimenTags.open()
                        }
                    }

                }
            }
            states: [
                State {
                    name: "enabled"
                    PropertyChanges { target: tabOvStTiFc; enabled: true; }
                },
                State {
                    name: "disabled"
                    PropertyChanges { target: tabOvStTiFc; enabled: false; }
                }
            ]
        } // tabOvStTiFc
    } // tvActions
    TrawlBackdeckButton {
        id: btnSpecialAction
        text: qsTr("Special\nAction")
        state: qsTr("disabled")
        onClicked: {
            if (!screens.busy)
                screens.push(Qt.resolvedUrl("SpecialActionsScreen.qml"))
                tbdSM.to_special_actions_state()
        }
        x: main.width - this.width - 52
        y: 20
    } // btnSpecialAction

    FramNumPad {
        id: numPad
        x: 630
        y: 500
        state: qsTr("weights")

        onNumpadok: {
            if (this.stored_result)
                var numPadValue = this.stored_result

            var tab = tvActions.getTab(tvActions.currentIndex)
            var value;
            if (tab.active) {
                switch (tab) {
                    case tabSexLength:
                        // If numPadValue is defined, parse it, if undefined, set to null
                        linealValue = numPadValue ? parseFloat(numPadValue) : null
//                        if (isNaN(linealValue)) linealValue = "";

                        if (fishSampling.actionMode == "modify") {
                            if (tvSpecimens.currentRow != -1) {
                                fishSampling.update_list_item("linealValue", linealValue)
                            }
                        } else if (fishSampling.actionMode == "add") {
                            fishSampling.add_list_item(linealValue, fishSampling.sex)
                        }
//                        tab.item.tfLineal.text = linealValue ? linealValue.toFixed(1) : ""
                        break;

                    case tabWeightAge:
                        var property;

                        // Check if the value is a float
                        value = numPadValue ? parseFloat(numPadValue) : null
                        if (value != null) {
                            if (value % 1 != 0) {
                                console.info('float value obtained')

                                // We have a float, so it must be a weight
                                tab.item.tfWeight.forceActiveFocus()
                                tab.item.tfWeight.selectAll()
                            }
                        }

                        if (tab.item.tfWeight.focus) {
                            property = "weight"
                            value = numPadValue ? parseFloat(numPadValue) : null
                        } else if (tab.item.tfAge.focus) {
                            property = "ageNumber"
                            value = numPadValue ? parseInt(numPadValue) : null
                        }
//                        if (isNaN(value)) value = null;

                        if (tvSpecimens.currentRow != -1) {
                            fishSampling.update_list_item(property, value)
                            if (property == "weight") {
                                tab.item.tfWeight.text = value ? value.toFixed(3) : ""
                            } else {
                                tab.item.tfAge.text = value ? value : ""
                            }
                            root.forceActiveFocus()
                        }
                        break;

                    case tabOvStTiFc:
//                        if (numPadValue == undefined) numPadValue = null;
                        var newValue = numPadValue ? parseInt(numPadValue) : null
                        var tvSamples = tab.item.tvSamples;
                        var deletedSubSpecimen = false;
//                        console.info('newValue: ' + newValue)

                        tvSamples.selection.forEach (  // Works - requires tvSamples alias inside Item
                            function(rowIndex) {
                                var item = tvSamples.model.get(rowIndex)
                                var specimenItem = tvSpecimens.model.get(tvSpecimens.currentRow)
                                var id = item["type"].replace("Number", "SpecimenId")
                                var type = item["type"]
                                var specimenId = specimenItem[id]
                                var existingValue = item["value"]
//                                console.info('id: ' + id)
//                                console.info('specimenId: ' + specimenId)
//                                console.info('spec: ' + JSON.stringify(specimenItem))
//                                console.info('item: ' + JSON.stringify(item))

//                                return
                                if (existingValue) {
                                    if (existingValue.toString().length > 0) {
                                        dlgOvaryEtcUpdate.measurement = item["type"]
                                        dlgOvaryEtcUpdate.value = numPadValue
                                        dlgOvaryEtcUpdate.errors = "You already have a Tag ID Assigned:\n\n\t" + existingValue
                                        dlgOvaryEtcUpdate.open()
                                    } else {
//                                        console.info('existing value whose length <=0')
                                        if (typeof newValue == 'number') {
                                            fishSampling.update_list_item(item["type"], newValue)
                                            tvSamples.model.setProperty(rowIndex, "value", newValue)
                                        } else {
                                            fishSampling.delete_sub_specimen(specimenId)
                                            tvSamples.model.setProperty(rowIndex, "value", null)
                                            deletedSubSpecimen = true;
                                        }
                                    }
                                } else {
                                    if (typeof newValue == 'number') {
//                                        console.info('OK updating')
                                        fishSampling.update_list_item(item["type"], newValue)
                                        tvSamples.model.setProperty(rowIndex, "value", newValue)
                                    } else {
//                                        console.info('OK deleting')
                                        fishSampling.delete_sub_specimen(specimenId)
                                        tvSamples.model.setProperty(rowIndex, "value", null)
                                        deletedSubSpecimen = true;
                                    }
                                }

                                // Need to update the tvSpecimens model to remove references to the delete subspecimen
                                if (deletedSubSpecimen) {
                                    tvSpecimens.model.setProperty(stateMachine.specimen["row"], type, null)
                                    tvSpecimens.model.setProperty(stateMachine.specimen["row"], id, null)
                                }
                            }
                        )
                        if ((tvSamples.currentRow != -1) & (tvSamples.currentRow < tvSamples.model.count-1)) {
                            tvSamples.selection.clear()
                            tvSamples.selection.select(tvSamples.currentRow)
                        }
                        break;
                }
            }
//            if (tab != tabOvStTiFc)
//                numPad.textNumPad.text = 0
        }
    } // numPad

    ColumnLayout {

        id: cllPrintCounts
        anchors.top: tvActions.bottom
        anchors.topMargin: 10
        anchors.right: tvActions.right
        spacing: 10
        ExclusiveGroup {
            id: egPrinters
        }

        TrawlBackdeckButton {
            id: btnPrintLabel
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            text: qsTr("Print\nLabel")
            state: qsTr("disabled")
            onClicked: {
                var comport = btnPrinter1.checked ? serialPortManager.printers["Printer 1"] :
                                                    serialPortManager.printers["Printer 2"]

                var tvSamples = tabOvStTiFc.item.tvSamples;
                tvSamples.selection.forEach (
                    function(rowIndex) {
                        var item = tvSamples.model.get(rowIndex);
                        var value = item["value"];
                        var action = item["type"];
                        if ((value != null) && (value != ""))
                            fishSampling.print_job(comport, action, value)
                    }
                )

            }
        } // btnPrintLabel
        TrawlBackdeckButton {
            id: btnPrinter1
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
//            text: "Printer 1\n(" + settings.printer1 + ")"
            text: "Printer 1\n(" + serialPortManager.printers["Printer 1"] + ")"
            checked: true
            checkable: true
            exclusiveGroup: egPrinters
            onClicked: {
                settings.currentPrinter = serialPortManager.printers["Printer 1"]
            }
        } // btnPrinter1
        TrawlBackdeckButton {
            id: btnPrinter2
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            text: "Printer 2\n(" + serialPortManager.printers["Printer 2"] + ")"
            checkable: true
            exclusiveGroup: egPrinters
            onClicked: {
                settings.currentPrinter = serialPortManager.printers["Printer 2"]
            }
        } // btnPrinter2

        ColumnLayout {
//            spacing: 5
            Label {
                text: qsTr("Sex-Len #")
                font.pixelSize: 20
                Layout.preferredHeight: 30
                Layout.preferredWidth: 90
                horizontalAlignment:  Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfTotalFish
                text: qsTr("")
                font.pixelSize: 20
                Layout.preferredHeight: 30
                Layout.preferredWidth: 100
            }
        }
        ColumnLayout {
//            spacing: 5
            Label {
                text: qsTr("Age-Wgt #")
                font.pixelSize: 20
                Layout.preferredHeight: 30
                Layout.preferredWidth: 90
                horizontalAlignment:  Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
            TrawlBackdeckTextFieldDisabled {
                id: tfProtocolFish
                text: qsTr("")
                font.pixelSize: 20
                Layout.preferredHeight: 30
                Layout.preferredWidth: 100
            }
        }

    } // Printing Items

    RowLayout {
        id: rwlFinishedButtons
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        spacing: 10
        TrawlBackdeckButton {
            id: btnNotes
            text: qsTr("Note")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: {
                dlgNote.reset(tvSpecimens)
                dlgNote.open()
                return;
                var results = notes.getNote(dlgNote.primaryKey)
            }
        }
        TrawlBackdeckButton {
            id: btnBack
            text: qsTr("<<")
            Layout.preferredWidth: 60
            Layout.preferredHeight: this.height
            onClicked: {

                // Check to ensure that the weight and age are populated
                var weight = tabWeightAge.item.tfWeight.text
                weight = weight ? parseFloat(weight) : null
                var age = tabWeightAge.item.tfAge.text
                age = age ? parseInt(age) : null
                var success1 = true;
                if (tvActions.currentIndex == 1) {
                    success1 = qaqc.fishSamplingLeaveAgeWeightTabCheck(weight, age)
                }
                var success2 = qaqc.fishSamplingSameSexCheck()
                if (success1 && success2) {
                    screens.pop();
                } else {
                    if ((!success1) && (!success2)) {
                        dlgOkayCancel.target = "processCatch"
                        var msg = "Your Weight or Age is empty\n"
                        msg  = msg + "You have " + fishSampling.model.count + " specimens that are all the same sex"
                        dlgOkayCancel.message = msg
                        dlgOkayCancel.open()
                    } else if (!success1) {
                        dlgOkayCancel.target = "processCatch"
                        dlgOkayCancel.message = "Your Weight or Age is empty"
                        dlgOkayCancel.open()
                    } else if (!success2) {
                        dlgSameSexCheck.specimenCount = fishSampling.model.count
                        dlgSameSexCheck.open()
                    }
                }
            }
        } // btnDone
    } // btnBack

    TrawlNoteDialog { id: dlgNote }

    FramConfirmDialog {
        id: dlgConfirm
        visible: false
//        action_label: "override the age\nbarcode number?"

        auto_hide: false
        auto_label: false

//        dlgConfirm.hide()

        onCancelledFunc: {
            this.hide()
        }

        onConfirmedFunc: {
            if (action_name == "override barcode") {
                var tab = tvActions.getTab(1)
//                tab.item.tfAge.text
//            } else if (action_name == "take subsample") {
//                tvBaskets.selection.forEach(
//                    function(idx) {
//                        weighBaskets.update_list_item(idx, "subsample", "Yes")
//                        weighBaskets.lastSubsampleBasket = idx + 1
//                    }
//                )

            } else if (action_name == "delete specimen") {
                tvSpecimens.selection.forEach (
                    function(rowIndex) {
                        fishSampling.delete_list_item(rowIndex)
                        var newIndex = rowIndex - 1;
                        if ((newIndex >= 0) & (newIndex < tvSpecimens.model.count)) {
                            tvSpecimens.selection.clear()
                            tvSpecimens.currentRow = newIndex
                            tvSpecimens.selection.select(newIndex)
                        } else if (tvSpecimens.model.count == 0) {
                            btnDeleteEntry.state = qsTr("disabled")
                            btnModifyEntry.state = qsTr("disabled")
                            tabWeightAge.state = qsTr("disabled")
                            tabOvStTiFc.state = qsTr("disabled")
                            tvActions.currentIndex = 0
                        }
                    }
                )
                this.hide()

            } else if (action_name == "barcode errors") {

                fishSampling.errorChecks = false
                fishSampling.update_list_item("ageNumber", tabWeightAge.item.tfAge.text)
                this.hide()

            } else if (action_name == "weight error") {

                fishSampling.errorChecks = false
                fishSampling.update_list_item("weight", tabWeightAge.item.tfWeight.text)
                this.hide()

            } else if (action_name == "linealValue error") {

                fishSampling.errorChecks = false
                fishSampling.update_list_item("linealValue", tabSexLength.item.tfLineal.text)
                this.hide()

            } else if (action_name == "sex error") {

                fishSampling.errorChecks = false
                var sex;
                if (tabSexLength.item.btnFemale.checked)
                    sex = "F"
                else if (tabSexLength.item.btnMale.checked)
                    sex = "M"
                else
                    sex = "U"
                fishSampling.update_list_item("sex", sex)
                this.hide()

            } else if (acton_name == "printer failed") {



            } else if (action_name == "leave screen") {
                this.hide()
                screens.pop()

            }
        }
    } // FramConfirmDialog

    TrawlConfirmDialog {
        id: dlgRemoveSpecies
        property int speciesNumber: -1
        message: "You are about to delete specimen #" + speciesNumber + "\n\n"
        action: "Are you sure that you want to do this?"
        onAccepted: {
            tvSpecimens.selection.forEach (
                function(rowIndex) {
                    fishSampling.delete_list_item(rowIndex)
                    var newIndex = rowIndex - 1;
                    if ((newIndex >= 0) & (newIndex < tvSpecimens.model.count)) {
                        tvSpecimens.selection.clear()
                        tvSpecimens.currentRow = newIndex
                        tvSpecimens.selection.select(newIndex)
                    } else if (tvSpecimens.model.count == 0) {
                        stateMachine.specimen = null
                        fishSampling.mode = "Sex-Length"
                        btnDeleteEntry.state = qsTr("disabled")
                        btnModifyEntry.state = qsTr("disabled")
                        tvActions.currentIndex = 0
                    }
                }
            )
        }
    } // dlgRemoveSpecies
    TrawlDataEntryCheckDialog {
        id: dlgMeasurementTaken
        measurement: ""
        unit_of_measurement: ""
        onAccepted: {
            fishSampling.errorChecks = false
            if (fishSampling.actionMode == "add") {
                fishSampling.add_list_item(value, fishSampling.sex)
            } else if (fishSampling.actionMode == "modify") {
                fishSampling.update_list_item(measurement, value)
            }
        }
        onRejected: {
            fishSampling.actionMode = "add"
        }
    } // dlgMeasurementTaken
    TrawlDataEntryCheckDialog {
        id: dlgLinealAdd
        measurement: "Length"
        unit_of_measurement: "cm"
        onAccepted: {
            fishSampling.errorChecks = false
            fishSampling.add_list_item(value, fishSampling.sex)
        }
        onRejected: {
            fishSampling.actionMode = "add"
        }
    } // dlgLinealAdd
    TrawlDataEntryCheckDialog {
        id: dlgLinealUpdate
        measurement: "Length"
        unit_of_measurement: "cm"
        onAccepted: {
            fishSampling.errorChecks = false
            fishSampling.update_list_item("linealValue", value)
        }
        onRejected: {
            fishSampling.actionMode = "add"
            if (tvSpecimens.currentRow != -1) {
                var item = tvSpecimens.model.get(tvSpecimens.currentRow)
                var linealValue = item["linealValue"]
                tabSexLength.item.tfLineal.text = (typeof linealValue == 'number') ? parseFloat(linealValue).toFixed(1) : ""
                numPad.textNumPad.text = tabSexLength.item.tfLineal.text
            }
            tabSexLength.item.tfLineal.forceActiveFocus()
            tabSexLength.item.tfLineal.selectAll()
            numPad.textNumPad.selectAll()
        }
    } // dlgLinealUpdate
    TrawlDataEntryCheckDialog {
        id: dlgWeight
        measurement: "Weight"
        unit_of_measurement: "kg"
        onAccepted: {
//            console.info('accepted weight')
            fishSampling.errorChecks = false
            fishSampling.update_list_item("weight", value)

            if (tabWeightAge.item.tfWeight.activeFocus) {
                console.info('dlg active focus')
                numPad.textNumPad.text = tab.item.tfAge.text
//                    numPad.textNumPad.forceActiveFocus()
                tab.item.tfAge.forceActiveFocus()
                tab.item.tfAge.selectAll()
                numPad.textNumPad.selectAll()
            }
        }
        onRejected: {
            fishSampling.actionMode = "add"
            if (tvSpecimens.currentRow != -1) {
                var item = tvSpecimens.model.get(tvSpecimens.currentRow)
                var weight = item["weight"]
                tabWeightAge.item.tfWeight.text = (typeof weight == 'number') ? parseFloat(weight).toFixed(3) : ""
                numPad.textNumPad.text = tabWeightAge.item.tfWeight.text
            }
            tabWeightAge.item.tfWeight.forceActiveFocus()
            tabWeightAge.item.tfWeight.selectAll()
            numPad.textNumPad.selectAll()
        }
    } // dlgWeight
    TrawlDataEntryCheckDialog {
        id: dlgAge
        measurement: "Age Barcode ID"
        unit_of_measurement: ""
        onAccepted: {
            fishSampling.errorChecks = false
            fishSampling.update_list_item("ageNumber", value)
//            tabWeightAge.item.tfAge.deselect()
//            numPad.textNumPad.deselect()
//            root.forceActiveFocus()
        }
        onRejected: {
            fishSampling.actionMode = "add"
            if (tvSpecimens.currentRow != -1) {
                var item = tvSpecimens.model.get(tvSpecimens.currentRow)
                var age = item["ageNumber"]
                tabWeightAge.item.tfAge.text = (typeof age == 'number') ? parseInt(age) : ""
                numPad.textNumPad.text = tabWeightAge.item.tfAge.text
            }
            tabWeightAge.item.tfAge.forceActiveFocus()
            tabWeightAge.item.tfAge.selectAll()
            numPad.textNumPad.selectAll()
        }
    } // dlgAge
    TrawlDataEntryCheckDialog {
        id: dlgSexUpdate
        measurement: "Sex"
        unit_of_measurement: ""
        onAccepted: {
//            console.info('accepted sex')
            fishSampling.errorChecks = false
            fishSampling.update_list_item("sex", value)
        }
         onRejected: {
            fishSampling.actionMode = "add"
        }
   } // dlgSexUpdate
    TrawlDataEntryCheckDialog {
        id: dlgOvaryEtcUpdate
        measurement: ""
        unit_of_measurement: ""
        onAccepted: {
            var numPadValue = numPad.stored_result ? parseInt(numPad.stored_result) : null
            var tvSamples = tabOvStTiFc.item.tvSamples

            if (tvSamples.currentRow != -1) {
                var item = tvSamples.model.get(tvSamples.currentRow)

                if (typeof numPadValue == 'number') {
                    // Update the value of the sub specimen
                    fishSampling.update_list_item(item["type"], numPadValue)
                    tvSamples.model.setProperty(tvSamples.currentRow, "value", numPadValue)

                } else {
                    // Delete the sub-specimen
                    var specimenItem = tvSpecimens.model.get(tvSpecimens.currentRow)
                    var id = item["type"].replace("Number", "SpecimenId")
                    var type = item["type"]
                    var specimenId = specimenItem[id]
                    fishSampling.delete_sub_specimen(specimenId)
                    tvSamples.model.setProperty(tvSamples.currentRow, "value", "")
                    tvSpecimens.model.setProperty(stateMachine.specimen["row"], type, null)
                    tvSpecimens.model.setProperty(stateMachine.specimen["row"], id, null)

                }


//                if ((numPadValue) && (numPadValue != "0") && (numPadValue != 0)) {
//                    model_value = parseInt(numPadValue)
//                } else {
//                    model_value = null
//                }
//
//                fishSampling.update_list_item(item["type"], model_value)
//                tvSamples.model.setProperty(tvSamples.currentRow, "value", model_value)
            }
            fishSampling.actionMode = "add"
        }
         onRejected: {
            fishSampling.actionMode = "add"
        }
   } // dlgOvaryEtcUpdate
    TrawlConfirmDialog {
        id: dlgSameSexCheck
        height: 240
        property int specimenCount: -1
        message: "You have " + specimenCount + " specimens that are all the same sex\n\nDid you forget to switch the sex?\n"
        action: "Are you sure you want to leave Fish Sampling?"
        onAccepted: { screens.pop() }
        onRejected: {}
    } // dlgSameSexCheck
    TrawlConfirmDialog {
        id: dlgOkayCancel
        message: ""
        property string target: "test"
        onAccepted: {
            if (target == "tabSexLength") {
                fishSampling.activeTab = "Sex-Length"
            } else if (target == "processCatch") {
                screens.pop();
            } else {
            }
        }
        onRejected: {
            if (target == "tabSexLength") {
                fishSampling.activeTab = "Age-Weight"
            } else {
            }
        }
    }
    SpecimenTagsDialog {
        id: dlgSpecimenTags
    }
    TrawlOkayDialog {
        id: dlgOkay
        message: ""
        property string target: "test"
        onAccepted: {
            if (target == "tabOvStTiFc") {
            }
        }
        onRejected: {

        }

    }
}