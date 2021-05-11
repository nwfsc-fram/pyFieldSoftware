import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.0

import "../common"

Item {
    id: root
    property int maturityButtonWidth: 260
    property int categoricalButtonWidth: maturityButtonWidth;

    Component.onDestruction: {
        if (stateMachine.previousScreen == "fishsampling")
            tbdSM.to_fish_sampling_state()
        else if (stateMachine.previousScreen = "processcatch")
            tbdSM.to_process_catch_state()
    }

    Component.onCompleted: {
        var taxonId = stateMachine.species["taxonomy_id"]
        if (typeof taxonId != 'undefined') {
            var isSalmon = processCatch.checkSpeciesType("salmon", taxonId)
            var isCoral = processCatch.checkSpeciesType("coral", taxonId);
            var isSponge = processCatch.checkSpeciesType("sponge", taxonId);
            if (isSalmon) {
                root.state = qsTr("salmon")
            } else if (isCoral) {
                root.state = qsTr("corals")
            } else if (isSponge) {
                root.state = qsTr("sponge")
            } else {
                root.state = qsTr("measurement")
            }
        }
    }

    Connections {
        target: tvSamples.selection
        onSelectionChanged: selectionChanged()
    } // onSelectionChanged
    Connections {
        target: specialActions
//        onModelInitialized: selectFirstRow();
        onModelInitialized: selectWallaceIDRow();
    } // onModelInitializeed
    Connections {
        target: specialActions
        onSpecimenTypeChanged: changeSpecimenType();
    } // onSpecimenTypeChanged
    Connections {
        target: specialActions
        onPrinterStatusReceived: processPrinterStatus(comport, success, message)
    } // onPrinterStatusReceived

    function processPrinterStatus(comport, success, message) {
        if (!success) {
            msg.show(comport + " printing error: " + message)

        }
    }

    function changeSpecimenType() {
        if (specialActions.standardSurveySpecimen)
            btnAddSpecimen.state = qsTr("disabled")
        else
            btnAddSpecimen.state = qsTr("enabled")
    }

    function selectFirstRow() {
        if (tvSamples.model.count > 0) {
            tvSamples.currentRow = 0;
            tvSamples.selection.select(0);
        }
    }

    function selectWallaceIDRow() {
        var wallaceIDAction = "Otolith Age ID";
        for (var i=0; i < tvSamples.model.count; i++) {
            if (tvSamples.model.get(i)["specialAction"] === wallaceIDAction) {
               tvSamples.currentRow = i;
               tvSamples.selection.select(i);
               return;
            }
        }
        // Else, didn't find it, so select first row
        selectFirstRow();
    }

    function selectionChanged() {
        if ((tvSamples.model.count == 0) || (tvSamples.currentRow == -1)) {
            root.state = "measurement"
        } else {
            var index = tvSamples.currentRow;
            specialActions.rowIndex = index;        // for taking in automatic data feeds - barcode, scale, ...

            var data = tvSamples.model.get(index)
            root.state = qsTr(data["widgetType"])

            specialActions.rowWidgetType = data["widgetType"] // for taking in automatic data feeds

            var value = data["value"];
            var parentSpecimenNumber = data["parentSpecimenNumber"];
        }

        switch (root.state) {
            case "id":
//                numPad.textNumPad.text = value ? value : "";
                numPad.textNumPad.text = ""
                btnAssignTagId.state = qsTr("enabled")
                if (value)
                    btnPrintLabel.state = qsTr("enabled")
                else
                    btnPrintLabel.state = qsTr("disabled")
                break;
            case "measurement":
                numPad.textNumPad.text = value ? value : "";
                break;
            case "salmon":
                var keys = ["Salmon Stage", "Salmon Population", "Salmon Condition"]
                for (var i=0; i<keys.length; i++) {
                    for (var j=0; j<tvSamples.model.items.length; j++) {
                        if ((tvSamples.model.get(j)["specialAction"] == keys[i]) &&
                            (tvSamples.model.get(j)["parentSpecimenNumber"] == parentSpecimenNumber)) {
                            // Found It
                            var salmonValue = tvSamples.model.get(j)["value"];
                            switch (keys[i]) {
                                case "Salmon Stage":
                                    if (salmonValue == "Adult")
                                        btnAdultStage.checked = true;
                                    else if (salmonValue == "Sub-Adult")
                                        btnSubAdultStage.checked = true;
                                    else if (salmonValue == undefined) {
                                        btnAdultStage.checked = false;
                                        btnSubAdultStage.checked = false;
                                    }
                                    break;
                                case "Salmon Population":
                                    if (salmonValue == "Wild")
                                        btnWildPopulation.checked = true;
                                    else if (salmonValue == "Hatchery")
                                        btnHatcheryPopulation.checked = true;
                                    else if (salmonValue == undefined) {
                                        btnWildPopulation.checked = false;
                                        btnHatcheryPopulation.checked = false;
                                    }
                                    break;
                                case "Salmon Condition":
                                    if (salmonValue == "Alive")
                                        btnAliveCondition.checked = true;
                                    else if (salmonValue == "Dead")
                                        btnDeadCondition.checked = true;
                                    else if (salmonValue == undefined) {
                                        btnAliveCondition.checked = false;
                                        btnDeadCondition.checked = false;
                                    }
                                    break;
                            }
                            break;
                        }
                    }
                }
                break;
            // AB - this is not used in 2021
            case "coral":
                var keys = ["Coral Photograph", "Coral Whole Specimen", "Coral Specimen ID"]
                for (var i=0; i<keys.length; i++) {
                    for (var j=0; j<tvSamples.model.items.length; j++) {
                        if ((tvSamples.model.get(j)["specialAction"] == keys[i]) &&
                            (tvSamples.model.get(j)["parentSpecimenNumber"] == parentSpecimenNumber)) {
                            // Found It
                            var coralValue = tvSamples.model.get(j)["value"];
                            switch (keys[i]) {
                                case "Coral Photograph":
                                    if (coralValue == "Yes")
                                        btnPhotoTaken.checked = true;
                                    else if ((coralValue == "") || (coralValue == undefined))
                                        btnPhotoTaken.checked = false;
                                    break;
                                case "Coral Whole Specimen":
                                    if (coralValue == "Yes")
                                        btnWholeSpecimen.checked = true;
                                    else if ((coralValue == "") || (coralValue == undefined))
                                        btnWholeSpecimen.checked = false;
                                    break;
                                case "Coral Specimen ID":
                                    numPad.textNumPad.text = value ? value : "";
                                    break;
                            }
                            break;
                        }
                    }
                }
                break;
            // AB - this is not used in 2021
            case "sponge":
                var keys = ["Sponge Photograph", "Sponge Specimen ID"]
                for (var i=0; i<keys.length; i++) {
                    for (var j=0; j<tvSamples.model.items.length; j++) {
                        if ((tvSamples.model.get(j)["specialAction"] == keys[i]) &&
                            (tvSamples.model.get(j)["parentSpecimenNumber"] == parentSpecimenNumber)) {
                            // Found It
                            var spongeValue = tvSamples.model.get(j)["value"];
                            switch (keys[i]) {
                                case "Sponge Photograph":
                                    if (spongeValue == "Yes")
                                        btnPhotoTaken2.checked = true;
                                    else if ((spongeValue == "") || (spongeValue == undefined))
                                        btnPhotoTaken2.checked = false;
                                    break;
                                case "Sponge Specimen ID":
                                    numPad.textNumPad.text = value ? value : "";
                                    break;
                            }
                            break;
                        }
                    }
                }
                break;
            case "sex":
                switch (value) {
                    case "M":
                        btnMale.checked = true;
                        break;
                    case "F":
                        btnFemale.checked = true;
                        break;
                    case "U":
                        btnUnsex.checked = true;
                        break;
                    case undefined:
                        btnMale.checked = false;
                        btnFemale.checked = false;
                        btnUnsex.checked = false;
                        break;
                }
                break;
            // AB - added to capture the 'location' type for pyrosome project
            case "location":
                switch (value) {
                    case "Age_Wt":
                        btnAgeWt.checked = true;
                        break;
                    case "Length":
                        btnLen.checked = true;
                        break;
                    case "Catch":
                        btnCatch.checked = true;
                        break;
                    case undefined:
                        btnAgeWt.checked = false;
                        btnLen.checked = false;
                        btnCatch.checked = false;
                        break;
                }
                break;
            case "maturityLevel":
                switch (value) {
                    case "1 = Juvenile/Immature":
                        btnMaturity1.checked = true;
                        break;
                    case "2 = Adolescent/Maturing":
                        btnMaturity2.checked = true;
                        break;
                    case "3 = Adult/Mature":
                        btnMaturity3.checked = true;
                        break;
                    case "4 = Egg Cases Present":
                        btnMaturity4.checked = true;
                        break;
                    case undefined:
                        btnMaturity1.checked = false;
                        btnMaturity2.checked = false;
                        btnMaturity3.checked = false;
                        btnMaturity4.checked = false;
                }
                break;
            case "categoricalList":
                switch (value) {
                    case "Left":
                        btnLeftExcision.checked = true;
                        break;
                    case "Right":
                        btnRightExcision.checked = true;
                        break;
                    case "Unknown":
                        btnUnknownExcision.checked = false;
                        break;
                    case undefined:
                        btnLeftExcision.checked = false;
                        btnRightExcision.checked = false;
                        btnUnknownExcision.checked = false;
                }
                break;
            case "yesno":
                switch (value) {
                    case "Yes":
                        btnYes.checked = true;
                        break;
                    case "No":
                        btnNo.checked = true;
                        break;
                }
                break;
        }
    }

    function changeValue(type, key, value) {
        tvSamples.selection.forEach (
            function(rowIndex) {
                tvSamples.model.setProperty(rowIndex, "value", value)
                var item = tvSamples.model.get(rowIndex)
                if ((value === null) || (value === "") || (value === 0)) {
                    console.info('deleting')
                    specialActions.delete_specimen(item["specimenId"])
                } else {
                    console.info("upserting")
                    specialActions.upsert_specimen(rowIndex)
                }
            }
        )
    }

    function changeYesNo(value) {
        tvSamples.selection.forEach (
            function(rowIndex) {
                tvSamples.model.setProperty(rowIndex, "value", value)
                var item = tvSamples.model.get(rowIndex)
                if (value === null) {
                    specialActions.delete_specimen(item["specimenId"])
                } else {
                    specialActions.upsert_specimen(rowIndex)
                }
            }
        )
    }

    // AB - added to deal with location changes
    function changeLoc(location) {
        tvSamples.selection.forEach (
            function(rowIndex) {
                tvSamples.model.setProperty(rowIndex, "value", location)
                var item = tvSamples.model.get(rowIndex)
                if (location === null) {
                    specialActions.delete_specimen(item["specimenId"])
                    console.info('trying to delete')
                } else {
                    specialActions.upsert_specimen(rowIndex)
                    console.info("upserting")
                }
            }
        )
    }

    function changeSex(sex) {
        tvSamples.selection.forEach (
            function(rowIndex) {
                tvSamples.model.setProperty(rowIndex, "value", sex)
                var item = tvSamples.model.get(rowIndex)
                if (sex === null) {
                    specialActions.delete_specimen(item["specimenId"])
                    console.info('trying to delete')
                } else {
                    specialActions.upsert_specimen(rowIndex)
                    console.info("upserting")
                }
            }
        )
    }

    function changeMaturityLevel(level) {
        tvSamples.selection.forEach (
            function (rowIndex) {
                tvSamples.model.setProperty(rowIndex, "value", level)
                var item = tvSamples.model.get(rowIndex)
                if (level === null) {
                    specialActions.delete_specimen(item["specimenId"]);
                    console.info("trying to delete");
                } else {
                    specialActions.upsert_specimen(rowIndex)
                    console.info("upserting");
                }
            }
        )
    }

    function changeSalmonState(key, value) {
        tvSamples.selection.forEach (
            function(rowIndex) {
                var parentSpecimenNumber = tvSamples.model.get(rowIndex)["parentSpecimenNumber"];
                for (var i=0; i<tvSamples.model.count; i++) {
                    if ((tvSamples.model.get(i)["parentSpecimenNumber"] == parentSpecimenNumber) &&
                        (tvSamples.model.get(i)["specialAction"] == key)) {
                            tvSamples.model.setProperty(i, "value", value)
                            if ((value === null) || (value === ""))
                                specialActions.delete_specimen(tvSamples.model.get(i)["specimenId"])
                            else
                                specialActions.upsert_specimen(i)
                            break;
                    }
                }
            }
        )
    }

    function changeCoralValue(key, value) {
        var coralKey = "Coral " + key;
        if (typeof(value) === "boolean") {
            var coralValue = value ? "Yes" : ""
        } else
            var coralValue = value
        tvSamples.selection.forEach (
            function(rowIndex) {
                var parentSpecimenNumber = tvSamples.model.get(rowIndex)["parentSpecimenNumber"];
                for (var i=0; i<tvSamples.model.count; i++) {
                    if ((tvSamples.model.get(i)["parentSpecimenNumber"] == parentSpecimenNumber) &&
                        (tvSamples.model.get(i)["specialAction"] == coralKey)) {
                            tvSamples.model.setProperty(i, "value", coralValue)
                            if ((value === null) || (value === ""))
                                specialActions.delete_specimen(tvSamples.model.get(i)["specimenId"])
                            else
                                specialActions.upsert_specimen(i)
                            break;
                    }
                }
            }
        )
    }

    function changeSpongeValue(key, value) {
        var spongeKey = "Sponge " + key;
        if (typeof(value) === "boolean") {
            var spongeValue = value ? "Yes" : ""
        } else
            var spongeValue = value
        tvSamples.selection.forEach (
            function(rowIndex) {
                var parentSpecimenNumber = tvSamples.model.get(rowIndex)["parentSpecimenNumber"];
                for (var i=0; i<tvSamples.model.count; i++) {
                    if ((tvSamples.model.get(i)["parentSpecimenNumber"] == parentSpecimenNumber) &&
                        (tvSamples.model.get(i)["specialAction"] == spongeKey)) {
                            tvSamples.model.setProperty(i, "value", spongeValue)
                            if ((value === null) || (value === ""))
                                specialActions.delete_specimen(tvSamples.model.get(i)["specimenId"])
                            else
                                specialActions.upsert_specimen(i)
                            break;
                    }
                }
            }
        )
    }

    function changeMeasurement(rowIndex, numPadValue) {
        tvSamples.model.setProperty(rowIndex, "value", numPadValue);
        var item = tvSamples.model.get(rowIndex)
        if ((numPadValue === null) || (numPadValue === "")) {
            console.info('trying to delete')
            specialActions.delete_specimen(item["specimenId"])
        } else {
            if (item.specialAction === "Otolith Age ID" && specialActions.if_exist_otolith_id(item.value)) {
                var msg = "Barcode ID already scanned: " + item.value;
                dlgOkay.message = msg;
                dlgOkay.open();
                tvSamples.model.setProperty(rowIndex, "value", undefined);
            } else {
                console.info("Upserting")
                specialActions.upsert_specimen(rowIndex)
            }
        }
    }

    function changeCategoricalList(category) {
        tvSamples.selection.forEach (
            function (rowIndex) {
                tvSamples.model.setProperty(rowIndex, "value", category)
                var item = tvSamples.model.get(rowIndex)
                if (category === null) {
                    specialActions.delete_specimen(item["specimenId"]);
                    console.info("trying to delete");
                } else {
                    specialActions.upsert_specimen(rowIndex)
                    console.info("upserting");
                }
            }
        )
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
            readOnly: true
            Layout.preferredWidth: 300
        } // tfSpecies
        Label {
            id: lblSex
            text: qsTr("Sex")
            font.pixelSize: 20
            Layout.preferredWidth: 40
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfSex
            text: stateMachine.specimen["sex"] ? stateMachine.specimen["sex"] : ""
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 40
        } // tfSex
        Label {
            id: lblLength
            text: qsTr("Length")
            font.pixelSize: 20
            Layout.preferredWidth: 60
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfLength
            text: stateMachine.specimen["linealValue"] ? parseFloat(stateMachine.specimen["linealValue"]).toFixed(1) : ""
            font.pixelSize: 20
            readOnly: true
            Layout.preferredWidth: 60
        } // tfLength
    } // rwlHeader
    Label {
        id: lblSpecimenType
        y: rwlHeader.y
        anchors.right: parent.right
        anchors.rightMargin: 20
        text: specialActions.standardSurveySpecimen ? "Subsample Specimen" : "Non-Subsample Specimen"
        font.pixelSize: 24
        font.bold: true
        Layout.preferredWidth: 80
    } // lblSpecimenType

    TrawlBackdeckTableView {
        id: tvSamples
        x: rwlHeader.x
        y: rwlHeader.y + rwlHeader.height + 30
        width: 600
        height: main.height - rwlHeader.height - 130
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        model: specialActions.model

        TableViewColumn {
            role: "parentSpecimenNumber"
            title: "ID"
            width: 40
        } // parentSpecimenNumber
        TableViewColumn {
            role: "principalInvestigator"
            title: "PI"
            width: 120
        } // principalInvestigator
        TableViewColumn {
            role: "specialAction"
            title: "Special Action"
            width: 230
        } // specialAction
        TableViewColumn {
            role: "value"
            title: "Value"
            width: 210
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // value
    } // tvSamples

    RowLayout {
        id: rwlAddDeleteEntries
        anchors.left: tvSamples.left
        anchors.top: tvSamples.bottom
        anchors.topMargin: 10
        spacing: 10

        TrawlBackdeckButton {
            id: btnAddSpecimen
            text: qsTr("Add\nSpecimen")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            onClicked: {
                dlgSpecimen.open()
                if (dlgSpecimen.tvProjects.model.count > 0) {
//                    dlgSpecimen.tvProjects.selection.select(1)
                }

            }
        } // btnAddSpecimen
        TrawlBackdeckButton {
            id: btnAddCustomAction
            text: qsTr("Add Custom\nAction")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("disabled")
            onClicked: {
//                dlgTableView.show("Add Custom Action", "add action")
            }
        } // btnAddCustomAction
    } // rwlAddDeleteEntries

    RowLayout {
        id: rwlTagID
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        spacing: 10

        TrawlBackdeckButton {
            id: btnAssignTagId
            text: qsTr("Assign\nTag ID")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("disabled")
            onClicked: {
                var index = tvSamples.currentRow
                if (index != -1) {
                    var item = tvSamples.model.get(index)
                    var tagId = specialActions.get_tag_id(index)
                    if (tagId != "") {
                        tvSamples.model.setProperty(index, "value", tagId)
                        specialActions.upsert_specimen(index)
                        tvSamples.selection.select(index);
                    } else {

                        // Gosh, problems, we still have a duplicate tag id
                        var msg = "You have a duplicate tag: " + tagId + "\n\nPlease resort to manual tags"
                        dlgOkay.message = msg
                        dlgOkay.open()

                    }
                    numPad.textNumPad.text = ""
                }
            }
        } // btnAssignTagId
        TrawlBackdeckButton {
            id: btnPrintLabel
            text: qsTr("Print\nLabel")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("disabled")
            onClicked: {
                var comport = btnPrinter1.checked ? serialPortManager.printers["Printer 1"] :
                                                    serialPortManager.printers["Printer 2"]
//                var comport = settings.currentPrinter;

                tvSamples.selection.forEach (
                    function (rowIndex) {
                        var item = tvSamples.model.get(rowIndex);
                        var pi_id = item["piId"];
                        var value = item["value"];
                        var action = item["specialAction"]
                        if ((value != null) && (value != ""))
                            specialActions.printLabel(comport, pi_id, action, value)
                    }
                )
            }
        } // btnPrintLabel
    } // rwlTagID
    RowLayout {
        id: rwlCorals
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        spacing: 10

        TrawlBackdeckButton {
            id: btnPhotoTaken
            text: qsTr("Photograph\nTaken")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            onClicked: changeCoralValue("Photograph", this.checked)
        }
        TrawlBackdeckButton {
            id: btnWholeSpecimen
            text: qsTr("Whole\nSpecimen")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            onClicked: changeCoralValue("Whole Specimen", this.checked)
        }
    } // rwlCorals
    RowLayout {
        id: rwlSponges
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        spacing: 10

        TrawlBackdeckButton {
            id: btnPhotoTaken2
            text: qsTr("Photograph\nTaken")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            onClicked: changeSpongeValue("Photograph", this.checked)
        }
    } // rwlSponges
    GridLayout {
        id: glSalmonOptions
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        enabled: false
        visible: false
        columns: 2
        columnSpacing: 10
        rowSpacing: 30

        ExclusiveGroup {
            id: egMaturity
        }
        ExclusiveGroup {
            id: egBirthLocation
        }
        ExclusiveGroup {
            id: egDeadOrAlive
        }

        TrawlBackdeckButton {
            id: btnAdultStage
            text: qsTr("Adult")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egMaturity
            onClicked: changeSalmonState("Salmon Stage", "Adult")
        }
        TrawlBackdeckButton {
            id: btnSubAdultStage
            text: qsTr("Sub-Adult")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egMaturity
            onClicked: changeSalmonState("Salmon Stage", "Sub-Adult")
        }
        TrawlBackdeckButton {
            id: btnWildPopulation
            text: qsTr("Wild")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egBirthLocation
            onClicked: changeSalmonState("Salmon Population", "Wild")
        }
        TrawlBackdeckButton {
            id: btnHatcheryPopulation
            text: qsTr("Hatchery")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egBirthLocation
            onClicked: changeSalmonState("Salmon Population", "Hatchery")
        }
        TrawlBackdeckButton {
            id: btnDeadCondition
            text: qsTr("Dead")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egDeadOrAlive
            onClicked: changeSalmonState("Salmon Condition", "Dead")
        }
        TrawlBackdeckButton {
            id: btnAliveCondition
            text: qsTr("Alive")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checkable: true
            exclusiveGroup: egDeadOrAlive
            onClicked: changeSalmonState("Salmon Condition", "Alive")
        }
    } // glSalmonOptions
    ColumnLayout {
        id: colSex
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        spacing: 10
        ExclusiveGroup {
            id: egSex
        }

        TrawlBackdeckButton {
            id: btnMale
            text: qsTr("Male")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egSex
            onClicked: changeSex("M")
        }
        TrawlBackdeckButton {
            id: btnFemale
            text: qsTr("Female")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egSex
            onClicked: changeSex("F")
        }
        TrawlBackdeckButton {
            id: btnUnsex
            text: qsTr("Unsex")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egSex
            onClicked: changeSex("U")
        }
    } // colSex
        // AB - added for a location option (5/6/21)
    ColumnLayout {
        id: colLoc
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        spacing: 10
        ExclusiveGroup {
            id: egLoc
        }

        TrawlBackdeckButton {
            id: btnAgeWt
            text: qsTr("Age_Wt")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egLoc
            onClicked: changeLoc("Age_Wt")
        }
        TrawlBackdeckButton {
            id: btnLen
            text: qsTr("Length")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egLoc
            onClicked: changeLoc("Length")
        }
        TrawlBackdeckButton {
            id: btnCatch
            text: qsTr("Catch")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egLoc
            onClicked: changeLoc("Catch")
        }
    } // colLoc
    ColumnLayout {
        id: colYesNo
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        spacing: 10
        ExclusiveGroup {
            id: egYesNo
        }

        TrawlBackdeckButton {
            id: btnYes
            text: qsTr("Yes")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egYesNo
            onClicked: changeYesNo("Yes")
        }
        TrawlBackdeckButton {
            id: btnNo
            text: qsTr("No")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egYesNo
            onClicked: changeYesNo("No")
        }
    } // colYesNo
    FramNumPad {
        id: numPad
        x: tvSamples.x + tvSamples.width + 180
        y: 400
        state: "weights"
        onNumpadok: {
            if (this.stored_result)
                var numPadValue = this.stored_result
            if (tvSamples.model.count > 0) {
                tvSamples.selection.forEach (
                    function(rowIndex) {
                        if (numPadValue) {

                            if (numPadValue == 0) numPadValue = "";

                            if (root.state == "coral") {
                                changeCoralValue("Specimen ID", numPadValue);
                                return;
                            } else if (root.state == "sponge") {
                                changeSpongeValue("Specimen ID", numPadValue);
                                return;
                            }

                            changeMeasurement(rowIndex, numPadValue);
        //                        tvSamples.model.setProperty(rowIndex, "value", numPadValue)
                            // TODO (todd.hay) Write updated SpecialSampling sample number to the DB
                        } else {
                            changeMeasurement(rowIndex, null);
        //                        tvSamples.model.setProperty(rowIndex, "value", "")
                        }
                    }
                )
            }
        }
    } // numPad
    ColumnLayout {
        id: cllMaturityLevel
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        spacing: 10
        ExclusiveGroup { id: egMaturityLevel }
        TrawlBackdeckButton {
            id: btnMaturity1
            text: qsTr("1 = Juvenile/Immature")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: maturityButtonWidth
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egMaturityLevel
            onClicked: changeMaturityLevel(text)
        } // btnMaturity1
        TrawlBackdeckButton {
            id: btnMaturity2
            text: qsTr("2 = Adolescent/Maturing")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: maturityButtonWidth
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egMaturityLevel
            onClicked: changeMaturityLevel(text)
        } // btnMaturity2
        TrawlBackdeckButton {
            id: btnMaturity3
            text: qsTr("3 = Adult/Mature")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: maturityButtonWidth
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egMaturityLevel
            onClicked: changeMaturityLevel(text)
        } // btnMaturity3
        TrawlBackdeckButton {
            id: btnMaturity4
            text: qsTr("4 = Egg Cases Present")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: maturityButtonWidth
//            state: qsTr("enabled")
            state: stateMachine.specimen["sex"] === "M" ? false : true
            visible: stateMachine.specimen["sex"] === "M" ? false : true
            checkable: true
            checked: false
            exclusiveGroup: egMaturityLevel
            onClicked: changeMaturityLevel(text)
        } // btnMaturity4

    } // cllMaturityLevel
    ColumnLayout {
        id: cllCategoricalList
        anchors.left: tvSamples.right
        anchors.leftMargin: 20
        y: tvSamples.y
        spacing: 10
        ExclusiveGroup { id: egCategoricalList }
        TrawlBackdeckButton {
            id: btnLeftExcision
            text: qsTr("Left")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: categoricalButtonWidth
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egCategoricalList
            onClicked: changeCategoricalList(text)
        } // btnLeftExcision
        TrawlBackdeckButton {
            id: btnRightExcision
            text: qsTr("Right")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: categoricalButtonWidth
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egCategoricalList
            onClicked: changeCategoricalList(text)
        } // btnRightExcision
        TrawlBackdeckButton {
            id: btnUnknownExcision
            text: qsTr("Unknown")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: categoricalButtonWidth
            state: qsTr("enabled")
            checkable: true
            checked: false
            exclusiveGroup: egCategoricalList
            onClicked: changeCategoricalList(text)
        } // btnUnknownExcision
    } // cllCategoricalList

    RowLayout {
        id: rwlActionButtons
        x: main.width - this.width - 20
        y: main.height - this.height - 20

        ExclusiveGroup {
            id: egPrinters
        }

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

        TrawlBackdeckButton {
            id: btnNotes
            text: qsTr("Note")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: {
                dlgNote.reset(tvSamples)
                dlgNote.open()
            }
        }
        TrawlBackdeckButton {
            id: btnBack
            text: qsTr("<<")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: screens.pop()
        }
    } // rwlActionButtons

    Dialog {
        id: dlgSpecimen
        width: 580
        height: 400
    //    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
        title: "Add Specimen"
    //    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

        property alias tvProjects: tvProjects
        property string measurement: "Length"
        property real value: 20.0
        property string unit_of_measurement: "cm"
        property string errors: "The following errors were encountered:"
        property string action: "Do you want to keep this value?"

        onAccepted: {
            if (tvProjects.currentRow != -1) {
                var item = tvProjects.model.get(tvProjects.currentRow);
//                for (var i=0; i<parseInt(tfCount.text); i++) {
//                    specialActions.add_model_item(item["piId"], item["planId"], 1);
//                }
                specialActions.add_model_item(item["piId"], item["planId"], parseInt(tfCount.text));
            }
        }
        onRejected: {  }

        contentItem: Rectangle {
    //        color: SystemPaletteSingleton.window(true)
            color: "#eee"
            Label {
                id: lblAddSpecimen
                anchors.top: parent.top
                anchors.topMargin: 20
//                anchors.horizontalCenter: parent.horizontalCenter
                x: 20
                text: "Add Project Specimen"
                font.pixelSize: 24
            } // lblAddSpecimen
            RowLayout {
                id: rwlCount
                x: parent.width - this.width - 20
                y: 20
                spacing: 20
                Label {
                    id: lblCount
                    text: "Count"
                    font.pixelSize: 24
                    Layout.preferredWidth: this.width
                } // lblCount
                TextField {
                    id: tfCount
                    placeholderText: "#"
                    text: "1"
                    font.pixelSize: 24
                    Layout.preferredWidth: 40
                    onFocusChanged: {
//                        this.forceActiveFocus()
                        this.selectAll()
                    }
                } // tfCount
            }
            TrawlBackdeckTableView {
                id: tvProjects
                anchors.bottom: rwlButtons.top
                anchors.bottomMargin: 20
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width * 0.9
                height: 200

                selectionMode: SelectionMode.SingleSelection
                headerVisible: true
                horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
                model: specialActions.piProjectModel
                onClicked: {
                    if (this.model.get(row).value)
                        numPad.textNumPad.text = this.model.get(row).value
                    else
                        numPad.textNumPad.text = ""

                    if (this.currentRow != -1) {
                        btnAssignTagId.state = qsTr("enabled")
                        btnPrintLabel.state = qsTr("enabled")
                    } else {
                        btnAssignTagId.state = qsTr("disabled")
                        btnPrintLabel.state = qsTr("disabled")
                    }
                }
                TableViewColumn {
                    role: "principalInvestigator"
                    title: "PI"
                    width: 200
                } // principalInvestigator
                TableViewColumn {
                    role: "planName"
                    title: "Project"
                    width: 322
                } // projectName
            } // tvItems
            RowLayout {
                id: rwlButtons
                anchors.horizontalCenter: parent.horizontalCenter
                y: dlgSpecimen.height - this.height - 20
                spacing: 20
                TrawlBackdeckButton {
                    id: btnOkay
                    text: "Okay"
                    Layout.preferredWidth: this.width
                    Layout.preferredHeight: this.height
                    onClicked: { dlgSpecimen.accept() }
                } // btnOkay
                TrawlBackdeckButton {
                    id: btnCancel
                    text: "Cancel"
                    Layout.preferredWidth: this.width
                    Layout.preferredHeight: this.height
                    onClicked: { dlgSpecimen.reject() }
                } // btnCancel
            } // rwlButtons

    //        Keys.onPressed: if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) dlg.click(StandardButton.Retry)
            Keys.onEnterPressed: dlgSpecimen.accept()
            Keys.onReturnPressed: dlgSpecimen.accept()
            Keys.onEscapePressed: dlgSpecimen.reject()
            Keys.onBackPressed: dlgSpecimen.reject() // especially necessary on Android
        }
    }

    TrawlNoteDialog { id: dlgNote }

    TrawlOkayDialog {
        id: dlgOkay
        message: ""
        property string target: "test"
        onAccepted: {}
        onRejected: {}
    }

    FramTableViewDialog {
        id: dlgTableView
        visible: false
//        action_label: "override the age\nbarcode number?"

        auto_hide: true
        auto_label: false

//        dlgConfirm.hide()

        onCancelledFunc: {
            this.hide()
        }

        onConfirmedFunc: {
            if (action_name == "add specimen") {

            } else if (action_name == "add_action") {

            }
            this.hide()
        }
    }
    // AB - added colLoc information to each and a state for location - 5/6/21
    states: [
        State {
            name: "id"
            PropertyChanges { target: rwlTagID; enabled: true; visible: true}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: true; visible: true}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // id
        State {
            name: "measurement"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: true; visible: true}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // measurement
        State {
            name: "salmon"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: true; visible: true}
            PropertyChanges { target: numPad; enabled: false; visible: false}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // salmon
        State {
            name: "coral"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: rwlCorals; enabled: true; visible: true}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: true; visible: true}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // coral
        State {
            name: "sponge"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: true; visible: true; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: true; visible: true}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // sponge
        State {
            name: "sex"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: true; visible: true}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: false; visible: false}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // sex
        State {
            name: "location"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: false; visible: false}
            PropertyChanges { target: colLoc; enabled: true; visible: true}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // location
        State {
            name: "yesno"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: false; visible: false}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: true; visible: true}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // yesno
        State {
            name: "maturityLevel"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: false; visible: false}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: true; visible: true;}
            PropertyChanges { target: cllCategoricalList; enabled: false; visible: false;}
        }, // maturityLevel
        State {
            name: "categoricalList"
            PropertyChanges { target: rwlTagID; enabled: false; visible: false}
            PropertyChanges { target: colSex; enabled: false; visible: false}
            PropertyChanges { target: rwlCorals; enabled: false; visible: false}
            PropertyChanges { target: rwlSponges; enabled: false; visible: false; }
            PropertyChanges { target: glSalmonOptions; enabled: false; visible: false}
            PropertyChanges { target: numPad; enabled: false; visible: false}
            PropertyChanges { target: colLoc; enabled: false; visible: false}
            PropertyChanges { target: colYesNo; enabled: false; visible: false}
            PropertyChanges { target: cllMaturityLevel; enabled: false; visible: false;}
            PropertyChanges { target: cllCategoricalList; enabled: true; visible: true;}
        } // categoricalList
    ]
}