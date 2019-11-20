import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.1
import QtQml.Models 2.2
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0

ApplicationWindow {
    id: root
    title: "Sensor Data Feeds"
    width: 1100
    height: 768
    visible: false

    signal testingStateChanged()
    onTestingStateChanged: {

//        tvEvents.forceActiveFocus()
    }

    property variant parsed_sentence: {"column1": "", "column2": "", "column3": "", "column4": "", "column5": "",
                                        "column6": "", "column7": "", "column8": "", "column9": "", "column10": "",
                                        "column11": "", "column12": ""}
//    property variant parsed_sentence: Array(12).fill(0);

    property bool display_error_messages: false

    Component.onCompleted: {
        btnOperationsMode.checked = true
        sensorDataFeeds.displayMode = "operations"

        console.info("SensorDataFeeds.qml completed");
    }

    Connections {
        target: serialPortManager
        onDataReceived: dataReceived(com_port, data)
    } // serialPortManager.onDataReceived
    Connections {
        target: serialPortManager
        onExceptionEncountered: exceptionEncountered(com_port, msg, resolution, exception)
    } // serialPortManager.onExceptionEncountered
    Connections {
        target: serialPortManager
        onPortPlayStatusChanged: changePlayControlIcon(com_port, status)
    } // serialPortManager.onPortPlayStatusChanged
    Connections {
        target: serialPortManager
        onPortDataStatusChanged: changedPortDataStatus(com_port, status)
    } // serialPortManager.onPortDataStatusChanged
    Connections {
        target: sensorDataFeeds
        onDisplayModeChanged: displayModeChanged();
    } // sensorDataFeeds.onDisplayModeChanged
    Connections {
        target: serialPortManager
        onDuplicatePortFound: notifyOfDuplicatePort(com_port)
    } // serialPortManager.duplicatePortFound
    Connections {
        target: sensorDataFeeds
        onMeasurementsUomModelChanged: changedMeasurementsUomModel(value)
    } // serialPortManager.measurementsUomModelChanged

    Component {
        id: columnComponent
        TableViewColumn { width: 60 }
    } // columnComponent

    Component {
        id: cvsStartDisabled
        ButtonStyle {
            label: Item {
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height)
                        ctx.fillStyle = "gray";
                        ctx.beginPath();
                        ctx.moveTo(width/4, width/4);
                        ctx.lineTo(3*width/4, width/2);
                        ctx.lineTo(width/4, 3*width/4);
                        ctx.lineTo(width/4, width/4);
                        ctx.fill();
                    }
                }
            }
        }
    } // cvsStartDisabled
    Component {
        id: cvsStart
        ButtonStyle {
            label: Item {
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height)
                        ctx.fillStyle = "green";
                        ctx.beginPath();
                        ctx.moveTo(width/4, width/4);
                        ctx.lineTo(3*width/4, width/2);
                        ctx.lineTo(width/4, 3*width/4);
                        ctx.lineTo(width/4, width/4);
                        ctx.fill();
                    }
                }
            }
        }
    } // cvsStart
    Component {
        id: cvsStopDisabled
        ButtonStyle {
            label: Item {
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height)
                        ctx.fillStyle = "gray";
                        ctx.fillRect(width/4, height/4, width/2, height/2)
                        ctx.fill();
                    }
                }
            }
        }
    } // cvsStopDisabled
    Component {
        id: cvsStop
        ButtonStyle {
            label: Item {
                Canvas {
                    anchors.fill: parent
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height)
                        ctx.fillStyle = "red";
                        ctx.fillRect(width/4, height/4, width/2, height/2)
                        ctx.fill();
                    }
                }
            }
        }
    } // cvsStop


    Component {
        id: cvsStart3
        Rectangle {
            Button {
                width: 25
                height: 25
                anchors.centerIn: parent
                ButtonStyle {
                    label: Item {
                        Canvas {
                            anchors.fill: parent
                            onPaint: {
                                var ctx = getContext("2d");
                                ctx.clearRect(0, 0, width, width)
                                ctx.fillStyle = "green";
                                ctx.beginPath();
                                ctx.moveTo(width/4, width/4);
                                ctx.lineTo(3*width/4, width/2);
                                ctx.lineTo(width/4, 3*width/4);
                                ctx.lineTo(width/4, width/4);
                                ctx.fill();
                            }
                        }
                    }
                }
                onClicked: {
                    var com_port = sensorDataFeeds.sensorConfigurationModel.get(row).com_port
                    if (com_port != undefined) {
                        sensorDataFeeds.sensorConfigurationModel.setProperty(row, "start_stop_status", "started");
                        serialPortManager.start_thread(com_port)
                    }
                }
            }
        }
    } // cvsStart3
    Component {
        id: cvsStop3
        Button {
            width: 25
            height: 25
            anchors.centerIn: parent
            ButtonStyle {
                label: Item {
                    Canvas {
                        anchors.fill: parent
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.clearRect(0, 0, width, height)
                            ctx.fillStyle = "red";
                            ctx.fillRect(width/4, height/4, width/2, height/2)
                            ctx.fill();
                        }
                    }
                }
            }
            onClicked: {
                var com_port = sensorDataFeeds.sensorConfigurationModel.get(row).com_port
                if (com_port != undefined) {
                    sensorDataFeeds.sensorConfigurationModel.setProperty(row, "start_stop_status", "stopped");
                    serialPortManager.stop_thread(com_port)
                }
            }
        }
    } // cvsStop3

    Component {
        id: cvsStart2
        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, width)
                ctx.fillStyle = "green";
                ctx.beginPath();
                ctx.moveTo(width/4, width/4);
                ctx.lineTo(3*width/4, width/2);
                ctx.lineTo(width/4, 3*width/4);
                ctx.lineTo(width/4, width/4);
                ctx.fill();
            }
        }
    } // cvsStart2
    Component {
        id: cvsStop2
        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "red";
                ctx.fillRect(width/4, height/4, width/2, height/2)
                ctx.fill();
            }
        }
    } // cvsStop2

    Component {
        id: cvsMeatballGreen
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "lime"
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatballGreen
    Component {
        id: cvsMeatballRed
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "red"
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatballRed
    Component {
        id: cvsMeatballYellow
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "yellow"
                ctx.lineWidth = 1
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatballYellow
//    Component {
//        id: cvsMeatball
//        Canvas {
//            onPaint: {
//                var ctx = getContext("2d");
//                ctx.clearRect(0, 0, width, height)
//                ctx.fillStyle = meatball_color
//                ctx.lineWidth = 1
//                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
//                ctx.fill();
//            }
//        }
//    } // cvsMeatball
    toolBar: ToolBar {
        id: tbTools
        RowLayout {
            anchors.fill: parent
            ExclusiveGroup { id: egMode } // egMode

            // Mode
            Label {
                id: lblMode
                text: "Mode"
            } // lblMode
            Button {
                id: btnTestingMode
                text: qsTr("Testing")
                exclusiveGroup: egMode
                checkable: true
                checked: true
                onClicked: {
                    sensorDataFeeds.displayMode = "testing";
                }
            } // btnTestMode
            Button {
                id: btnOperationsMode
                text: qsTr("Operations")
                exclusiveGroup: egMode
                checkable: true
                checked: false
                onClicked: {
                    sensorDataFeeds.displayMode = "operations";
                }
            } // btnOperationsMode
            Button {
                id: btnMeasurementMode
                text: qsTr("Measurements")
                exclusiveGroup: egMode
                checkable: true
                checked: false
                onClicked: {
                    sensorDataFeeds.displayMode = "measurements";
                }
            } // btnMeasurementMode

            Item { Layout.preferredWidth: 70 }

            // Start/Stop Buttons
            Button {
                    id: btnStartAll
                    tooltip: qsTr("Start All Ports")
                    Layout.preferredHeight: 25
                    Layout.preferredWidth: 25
                    onClicked: {
                        for (var i=0; i < tvSensorConfiguration.model.count; i++) {
                            tvSensorConfiguration.model.setProperty(i, "start_stop_status", "started")
                        }
                        serialPortManager.start_all_threads()
                    }
                    style: cvsStart
//                    style: ButtonStyle {
//                        label: Item {
//                            Canvas {
//                                anchors.fill: parent
//                                onPaint: {
//                                    var ctx = getContext("2d");
//                                    ctx.clearRect(0, 0, width, height)
//                                    ctx.fillStyle = "green";
//                                    ctx.beginPath();
//                                    ctx.moveTo(width/4, height/4);
//                                    ctx.lineTo(3*width/4, height/2);
//                                    ctx.lineTo(width/4, 3*height/4);
//                                    ctx.lineTo(width/4, height/4);
//                                    ctx.fill();
//                                }
//                            }
//                        }
//                    }
                } // btnStartAll
            Button {
                    id: btnStopAll
                    tooltip: qsTr("Stop All Ports")
                    Layout.preferredHeight: 25
                    Layout.preferredWidth: 25
                    onClicked: {
                        var found_testing_com_port = false;
                        for (var i=0; i < tvSensorConfiguration.model.count; i++) {
                            tvSensorConfiguration.model.setProperty(i, "start_stop_status", "stopped")
                            if (tvSensorConfiguration.model.get(i).com_port == cbTestingComport.currentText)
                                found_testing_com_port = true;
                        }

                        // Change the testing displayMode com_port items back to their default
                        btnStart.enabled = true
                        btnStop.enabled = false
                        toggleComPortSettings(true)

                        // Delete the testing thread
                        // Don't delete the testing thread if that same com_port is already used in
                        // sensorConfigurationModel - that's the purpose of the found_testing_com_port test above
                        if (!found_testing_com_port)
                            serialPortManager.delete_thread(cbTestingComport.currentText)

                        serialPortManager.stop_all_threads()

                    }
                    style: cvsStop
//                    style: ButtonStyle {
//                            label: Item {
//                                Canvas {
//                                    anchors.fill: parent
//                                    onPaint: {
//                                        var ctx = getContext("2d");
//                                        ctx.clearRect(0, 0, width, height)
//                                        ctx.fillStyle = "red";
//                                        ctx.fillRect(width/4, height/4, width/2, height/2)
//                                        ctx.fill();
//                                    }
//                                }
//                            }
//                        }
                } // btnStopAll
            Button {
                id: btnClear
                text: qsTr("Clear Display")
                onClicked: {
                    switch (sensorDataFeeds.displayMode) {
                        case "testing":
                            tvTestSentences.model.clear()
                            break;
                        case "operations":
                            tvRawSentences.model.clear()
                            break;

                        case "measurements":
                            tvParsedSentences.model.clear()
                            break;

                    }
                }
            } // btnClear
            Button {
                id: btnShowErrors
                text: qsTr("Show Errors")
                checkable: true
                checked: false
                onClicked: {
                    if (checked) {
                        switch (sensorDataFeeds.displayMode) {
                            case "testing":
                                tvTestSentences.Layout.preferredHeight = rightPanel.height - tvErrorMessages.Layout.preferredHeight
                                break;
                            case "operations":
                                tvRawSentences.Layout.preferredHeight = rightPanel.height - tvErrorMessages.Layout.preferredHeight
                                break;
                        }
                        tvErrorMessages.visible = true
                        display_error_messages = true

                    } else {
                        switch (sensorDataFeeds.displayMode) {
                            case "testing":
                                tvTestSentences.Layout.preferredHeight = rightPanel.height
                                break;
                            case "operations":
                                tvRawSentences.Layout.preferredHeight = rightPanel.height
                                break;
                        }
                        tvErrorMessages.visible = false
                        display_error_messages = false
                    }
                }
            } // btnShowErrors

//            Item { Layout.preferredWidth: 70 }

            Item { Layout.fillWidth: true }

            Label {
                id: lblParseType
                text: "Parse Type:"
            } // lblParseType
            Item { Layout.preferredWidth: 10}
            ExclusiveGroup { id: egParseType }
            RadioButton {
                id: rbDelimited
                text: "Delimited"
                checked: true
                exclusiveGroup: egParseType
                onClicked: {
                    lblDelimiter.visible = true;
                    tfDelimiter.visible = true;
                }
            } // rbDelimited
            RadioButton {
                id: rbFixed
                text: "Fixed"
                checked: false
                exclusiveGroup: egParseType
                enabled: false
                onClicked: {
                    lblDelimiter.visible = false;
                    tfDelimiter.visible = false;
                }
            } // rbFixed
            Item { Layout.preferredWidth: 20 }
            Label {
                id: lblDelimiter
                text: "Delimiter:"
            } // lblDelimiter
            TextField {
                id: tfDelimiter
                text: ","
                Layout.preferredWidth: 20
                onFocusChanged: {
                    selectAll()
                }
            } // tfDelimiter

//            CheckBox {
//                id: cbParsed
//                text: "Parsed"
//                checked: false
//            } // cbParsed
//            ToolButton {
//                text: qsTr("\u25C0 %1").arg(Qt.application.name)
//                enabled: stack.depth > 1
//                onClicked: stack.pop()
//            }
//            Switch {
//                checked: true
//            }
        }
    }

    function exceptionEncountered(com_port, msg, resolution, exception) {

        var dNow = new Date();
        var date_time = dNow.getMonth()+1 + '/' + dNow.getDate() + '/' + dNow.getFullYear() + ' ' +
            ('0' + dNow.getHours()).slice(-2) + ':' + ('0' + dNow.getMinutes()).slice(-2) + ':' +
            ('0' + dNow.getSeconds()).slice(-2);

        var item = {"date_time": date_time,
                    "com_port": com_port,
                    "message": msg,
                    "resolution": resolution,
                    "exception": exception}
        sensorDataFeeds.errorMessagesModel.insert(0, item);

        if (cbTestingComport.currentText == com_port) {
            btnStart.enabled = true;
            btnStop.enabled = false;
            toggleComPortSettings(true);
            serialPortManager.delete_thread(com_port);
        }

        return;

//        switch (sensorDataFeeds.displayMode) {
//            case "testing":
//                sensorDataFeeds.errorMessagesModel.insert(0, {"sentence": msg})
//                break;
//            case "operations":
//                sensorDataFeeds.rawSentencesModel.insert(0, {"sentence": msg})
//                break;
//
//            case "measurements":
//                break;
//        }
    }

    function dataReceived(com_port, data) {

        switch (sensorDataFeeds.displayMode) {
            case "testing":

                if ((cbTestingComport.currentText == com_port) &
                    (!btnStart.enabled)) {
                    sensorDataFeeds.testSentencesModel.insert(0, {"sentence": data})
                }
                break;

            case "operations":

                if ((tvSensorConfiguration.model.count > 0) & (tvSensorConfiguration.currentRow != -1)) {
                    var selected_com_port = tvSensorConfiguration.model.get(tvSensorConfiguration.currentRow).com_port
                    if (selected_com_port == com_port) {
                        sensorDataFeeds.rawSentencesModel.insert(0, {"sentence": data})
                        if (sensorDataFeeds.rawSentencesModel.count > 500) {
                            sensorDataFeeds.rawSentencesModel.clear();
                        }
                    }
                }
                break;

            case "measurements":

                if ((tvSensorConfiguration.model.count > 0) & (tvSensorConfiguration.currentRow != -1)) {
                    var selected_com_port = tvSensorConfiguration.model.get(tvSensorConfiguration.currentRow).com_port
                    if (selected_com_port == com_port) {
                        var index;
                        var sentence_type;
                        var item;
                        var column1;
                        if (rbDelimited.checked) {
                            var delimiter = tfDelimiter.text
                            var sentence_fields = data.split(delimiter)
                            if (sentence_fields.length > 0) {

                                // Check if the table has enough columns for this parsed sentence
                                if (tvParsedSentences.columnCount < sentence_fields.length) {
                                    var columns_to_add = sentence_fields.length - tvParsedSentences.columnCount;

                                    // Dynamically adding columns to a TableView is described here:
                                    // http://stackoverflow.com/questions/27230818/qml-tableview-with-dynamic-number-of-columns
                                    var count = tvParsedSentences.columnCount;
                                    var new_column;
                                    var new_role;
                                    var tvc;
                                    for (var i=0; i < columns_to_add; i++) {
                                        new_column = parseInt(count + i + 1).toString();
                                        new_role = "column" + new_column;
                                        item = {"role": new_role,
                                                "title": new_column}
                                        tvc = columnComponent.createObject(tvParsedSentences, item)
                                        sensorDataFeeds.parsedSentencesModel.add_role_name(new_role)
                                        tvParsedSentences.addColumn(tvc)
                                    }
                                }

                                for (var i=0; i < tvParsedSentences.columnCount; i++) {
                                    if (i in sentence_fields)
                                        parsed_sentence["column"+parseInt(i+1).toString()] = sentence_fields[i]
                                    else
                                        parsed_sentence["column"+parseInt(i+1).toString()] = ""
                                }

                                sentence_type = sentence_fields[0]
                                if (tfSubstr.text == "") {
                                    index = sensorDataFeeds.parsedSentencesModel.get_item_index("column1", sentence_type)
                                } else {
                                    index = -1
                                    sentence_type = tfSubstr.text
                                    for (var i=0; i < sensorDataFeeds.parsedSentencesModel.count; i++) {
                                        item = sensorDataFeeds.parsedSentencesModel.get(i);
                                        column1 = item.column1
                                        if (column1.indexOf(sentence_type) >= 0) {
                                            index = i;
                                            break;
                                        }
                                    }
                                }

                                if (index != -1) {
                                    sensorDataFeeds.parsedSentencesModel.replace(index, parsed_sentence)
                                } else {
                                    sensorDataFeeds.parsedSentencesModel.insert(0, parsed_sentence)
                                }
//                                tvParsedSentences.resizeColumnsToContents()
                            }
                        } else if (rbFixed.checked) {

//                            sensorDataFeeds.rawSentencesModel.insert(0, {"sentence": data})
                        }


                    }
                }
                break;
        }
    }

    function displayModeChanged() {

        switch (sensorDataFeeds.displayMode) {
            case "testing":
                leftPanel.width = 150;

                lblParseType.visible = false;
                rbDelimited.visible = false;
                rbFixed.visible = false;
                lblDelimiter.visible = false;
                tfDelimiter.visible = false;

                tvTestSentences.visible = true
                tvSensorConfiguration.visible = false;
                tvRawSentences.visible = false
                tvErrorMessages.visible = display_error_messages
                tvParsedSentences.visible = false

                btnShowErrors.visible = true

                cllComportSettings.visible = true;
                cllComportSettings.anchors.top = leftPanel.top;
                cllComportSettings.anchors.topMargin = 20;

                cllTestingComport.visible = true;
                cllOperationsComport.visible = false;

                btnStartAll.visible = false;
                btnStopAll.visible = false;

                rwlStartStopButtons.visible = true;
                rwlAddUpdateComPortButtons.visible = false;

                glMatchingData.visible = false;
                rwlModifyMatchings.visible = false;
                tvMatchings.visible = false;
                cllReorderButtons.visible = false;

                toggleComPortSettings(btnStart.enabled);

                break;
            case "operations":
                leftPanel.width = 350;

                lblParseType.visible = false;
                rbDelimited.visible = false;
                rbFixed.visible = false;
                lblDelimiter.visible = false;
                tfDelimiter.visible = false;

                tvSensorConfiguration.visible = true
                tvTestSentences.visible = false
                tvRawSentences.visible = true
                tvParsedSentences.visible = false

                btnShowErrors.visible = true
                tvErrorMessages.visible = display_error_messages

                cllComportSettings.visible = true;
                cllComportSettings.anchors.top = tvSensorConfiguration.bottom
                cllComportSettings.anchors.topMargin = 20

                cllTestingComport.visible = false;
                cllOperationsComport.visible = true;

                btnStartAll.visible = true;
                btnStopAll.visible = true;

                rwlStartStopButtons.visible = false;
                rwlAddUpdateComPortButtons.visible = true;

                toggleComPortSettings(true);

                glMatchingData.visible = false;
                rwlModifyMatchings.visible = false;
                tvMatchings.visible = false;
                cllReorderButtons.visible = false;

                break;
            case "measurements":
                leftPanel.width = 350;

                lblParseType.visible = true;
                rbDelimited.visible = true;
                rbFixed.visible = true;
                lblDelimiter.visible = true;
                tfDelimiter.visible = true;

                tvSensorConfiguration.visible = true
                tvTestSentences.visible = false
                tvRawSentences.visible = false
                tvParsedSentences.visible = true
                tvErrorMessages.visible = false;
                btnShowErrors.visible = false;

                btnStartAll.visible = false;
                btnStopAll.visible = false;

                cllComportSettings.visible = false;
                rwlStartStopButtons.visible = false;
                rwlAddUpdateComPortButtons.visible = false;

                glMatchingData.visible = true;
                rwlModifyMatchings.visible = true;
                tvMatchings.visible = true;
                cllReorderButtons.visible = true;

                break;
        }
    }

    function changePlayControlIcon(com_port, status) {

        if (com_port != null) {
            var index = tvSensorConfiguration.model.get_item_index("com_port", com_port);
            if (index != -1) {
                if (tvSensorConfiguration.model.get(index).start_stop_status != status) {
                    tvSensorConfiguration.model.setProperty(index, "start_stop_status", status);
                }
            }
        }
    }

    function changedPortDataStatus(com_port, status) {
        var index = tvSensorConfiguration.model.get_item_index("com_port", com_port);
        if (index != -1) {
            sensorDataFeeds.sensorConfigurationModel.setProperty(index, "data_status", status)
        }
    }

    function getMeatballColor(status) {
        switch (status) {
            case "red": return cvsMeatballRed
            case "green": return cvsMeatballGreen
            case "yellow": return cvsMeatballYellow
            default: return cvsMeatballRed
        }
    }

    function notifyOfDuplicatePort(com_port) {
        dlgOkay.message = "You selected an already used COM port, " +
            "please select another\n\n" + com_port
        dlgOkay.open()
    }

    function changedMeasurementsUomModel(value) {
        var index = cbMeasurement.find(value);
        if (index != -1) {
            cbMeasurement.currentIndex = index;
        }
    }

    function createMatchingItem(action) {

        if ((tfEquipment.text != "") &&
                    (tfSentence.text != "") &&
                    (tfField.text != "") &&
                    (btnLineEnding.text != "") &&
                    (cbMeasurement.currentText != "")) {

            var index = sensorDataFeeds.equipmentModel.get_item_index("equipment", tfEquipment.text)
            if (index != -1)
                var equipment_id = sensorDataFeeds.equipmentModel.get(index).equipment_id;
            else
                return null;

            index = sensorDataFeeds.measurementsUnitsOfMeasurementModel
                .get_item_index("text", cbMeasurement.currentText)
            if (index != -1) {
                var measurement_lu_id =
                sensorDataFeeds.measurementsUnitsOfMeasurementModel.get(index).lookup_id
            } else
                return null;

            var fixed_or_delimited = rbDelimited.checked ? "delimited" : "fixed"

            // TODO Todd Hack below for line_ending - need to clean up - why having to escape \r\n?
            var item = {"equipment_id": equipment_id,
                        "equipment": tfEquipment.text,
                      "line_starting": tfSentence.text,
                      "is_line_starting_substr": (tfSubstr.text == "") ? false : true,
                      "fixed_or_delimited": fixed_or_delimited,
                      "delimiter": tfDelimiter.text,
                      "field_position": parseInt(tfField.text),
                      "start_position": -1,
                      "end_position": -1,
                      "line_ending": btnLineEnding.text,
                      "measurement": cbMeasurement.currentText,
                      "measurement_lu_id": measurement_lu_id,
                      "priority": sensorDataFeeds.measurementConfigurationModel.count+1}

            if (action == "update") {
                var row = tvMatchings.currentRow;
                if (row != -1) {
                    item["parsing_rules_id"] = sensorDataFeeds.measurementConfigurationModel.get(row).parsing_rules_id;
                    if (item["parsing_rules_id"] == undefined) return null;
                } else {
                    return null;
                }
            }
//            console.info('row: ' + row + ', item: ' + JSON.stringify(item))
            return item;
        } else
            return null;
    }

    function toggleComPortSettings(status) {
        cbTestingComport.enabled = status;
        cbBaudRate.enabled = status;
        cbDataBits.enabled = status;
        cbParity.enabled = status;
        cbStopBits.enabled = status;
        cbFlowControl.enabled = status;
    }

    SplitView {
        id: sv
        width: parent.width
        height: parent.height

        Rectangle {
            id: leftPanel
            width: 350
            color: SystemPaletteSingleton.window(true)

            TableView {

                id: tvSensorConfiguration
                width: parent.width
                height: 320
                TableViewColumn {
                    title: ""
                    role: "data_status"
                    width: 30
                    delegate: Component {
                        Loader {
                            anchors.fill: parent
                            sourceComponent: getMeatballColor(styleData.value)
                        }
                    }
                } // data_status
                TableViewColumn {
                    id: tvcStartStopStatus
                    title: ""
                    role: "start_stop_status"
                    width: 40
//                    delegate: Component {
//                        Loader {
//                            property int row: styleData.row
//                            anchors.fill: parent
//                            sourceComponent: (styleData.value == "started") ? cvsStop : cvsStart
//                        }
//                    }
                    delegate: Item {
                        Button {
                            width: 25
                            height: 25
                            anchors.centerIn: parent
//                            style: (styleData.row != -1) ? ((styleData.value == "started") ? bsStop : bsStart) : null

                            style: (styleData.row != -1) ? ((styleData.value == "started") ? cvsStop : cvsStart) : null
//                            style: ButtonStyle {
//                                label: (status == "started") ? cvsStop : cvsStart
//                            }
                            onClicked: {
                                var com_port = sensorDataFeeds.sensorConfigurationModel.get(styleData.row).com_port
                                if (com_port != undefined) {
                                    if (styleData.value == "stopped") {
                                        sensorDataFeeds.sensorConfigurationModel.setProperty(styleData.row, "start_stop_status", "started");
                                        serialPortManager.start_thread(com_port)
                                    } else if (styleData.value == "started") {
                                        sensorDataFeeds.sensorConfigurationModel.setProperty(styleData.row, "start_stop_status", "stopped");
                                        serialPortManager.stop_thread(com_port)
                                    }
                                }
                            }
                        }
                    }
                } // start_stop_status
                TableViewColumn {
                    title: "Port"
                    role: "com_port"
                    width: 50
                } // comport
                TableViewColumn {
                    title: "Moxa"
                    role: "moxa_port"
                    width: 50
                    delegate: Label {
                        text: styleData.value ? styleData.value : ""
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        color: styleData.selected ? "white" : "black"
                    }
                } // moxaport
                TableViewColumn {
                    title: "Equipment"
                    role: "equipment"
                    width: 135
                } // equipment
                TableViewColumn {
                    title: ""
                    role: "delete_row"
                    width: 40
                    delegate: Item {
                        Button {
                            width: 25
                            height: 25
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.horizontalCenter: parent.horizontalCenter
                            onClicked: {
                                var com_port = -1;
                                com_port = sensorDataFeeds.sensorConfigurationModel.get(styleData.row).com_port
                                if (com_port != -1) {
                                    sensorDataFeeds.sensorConfigurationModel.remove_row(com_port)
                                    tvSensorConfiguration.currentRow = -1
                                    tvSensorConfiguration.selection.clear()
                                }
                            }
                            style: ButtonStyle {
                                label: Item {
                                    Canvas {
                                        anchors.fill: parent
                                        onPaint: {
                                            var ctx = getContext("2d");
                                            ctx.lineWidth = 3;
                                            ctx.strokeStyle = Qt.rgba(0, 0, 0, 1);
                                            ctx.beginPath();
                                            ctx.moveTo(width/4, height/4);
                                            ctx.lineTo(3*width/4, 3*height/4);
                                            ctx.stroke();
                                            ctx.beginPath();
                                            ctx.moveTo(3*width/4, height/4);
                                            ctx.lineTo(width/4, 3*height/4);
                                            ctx.stroke();
                                        }
                                    }
                                }
                            }
                        }
                    }
                } // delete_row
                model: sensorDataFeeds.sensorConfigurationModel

                style: TableViewStyle {
                    rowDelegate: Rectangle {
                        height: 30
                        color: styleData.selected ? "skyblue" : (styleData.alternate? "#eee" : "#fff")
                    }
                }

                selection.onSelectionChanged: {

                    tvRawSentences.model.clear()
                    tvParsedSentences.model.clear()
                    tfSentence.text = "";
                    tfField.text = "";
                    if ((model.count > 0) & (currentRow != -1)) {
                        var item = model.get(currentRow)
                        tfEquipment.text = item.equipment;
                        btnUpdatePort.enabled = true;

                        cbOperationsComport.currentIndex = cbOperationsComport.find(item.com_port);
                        cbBaudRate.currentIndex = cbBaudRate.find(item.baud_rate.toString());
                        cbDataBits.currentIndex = cbDataBits.find(item.data_bits.toString());
                        cbParity.currentIndex = cbParity.find(item.parity);
                        cbStopBits.currentIndex = cbStopBits.find(item.stop_bits.toString());
                        cbFlowControl.currentIndex = cbFlowControl.find(item.flow_control);

                    } else {
                        tfEquipment.text = ""
                        btnUpdatePort.enabled = false;
                    }
                }
            } // tvSensorConfiguration
            ColumnLayout {
                id: cllComportSettings
                y: 20
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 20
                ColumnLayout {
                    id: cllTestingComport
                    anchors.horizontalCenter: parent.horizontalCenter
                    visible: false
                    Label {
                        id: lblTestingComport
                        text: "COM Port"
                    } // lblComport
                    ComboBox {
                        id: cbTestingComport
                        currentIndex: 0
//                        model: (Array.apply(0, Array(250)).map(function (x,y) {return y+1})).map(String)
                        model: sensorDataFeeds.comportModel
                        Layout.preferredWidth: 80
                    } // cbTestingComport
                } // cllTestingComport
                ColumnLayout {
                    id: cllOperationsComport
                    anchors.horizontalCenter: parent.horizontalCenter
                    Label {
                        id: lblOperationsComport
                        text: "COM Port"
                    } // lblOperationsComport
                    ComboBox {
                        id: cbOperationsComport
                        currentIndex: 0
//                        model: (Array.apply(0, Array(250)).map(function (x,y) {return y+1})).map(String)
                        model: sensorDataFeeds.comportModel
                        Layout.preferredWidth: 80
                    } // cbOperationsComport
                } // cllOperationsComport
                ColumnLayout {
                    id: cllBaudRate
                    anchors.horizontalCenter: parent.horizontalCenter
                    Label {
                        id: lblBaudRate
                        text: "Baud Rate"
                    } // lblBaudRate
                    ComboBox {
                        id: cbBaudRate
                        currentIndex: 5
                        model: [110, 300, 1200, 2400, 4800, 9600, 19200, 38400, 57600,
                          115200, 230400, 460800, 921600]
                        Layout.preferredWidth: cbTestingComport.width
                    } // cbBaudRate
                } // cllBaudRate
                ColumnLayout {
                    id: cllDataBits
                    anchors.horizontalCenter: parent.horizontalCenter
                    Label {
                        id: lblDataBits
                        text: "Data Bits"
                    } // lblDataBits
                    ComboBox {
                        id: cbDataBits
                        currentIndex: 3
                        model: [5, 6, 7, 8]
                        Layout.preferredWidth: cbTestingComport.width
                    } // cbDataBits
                } // cllDataBits
                ColumnLayout {
                    id: cllParity
                    anchors.horizontalCenter: parent.horizontalCenter
                    Label {
                        id: lblParity
                        text: "Parity"
                    } // lblParity
                    ComboBox {
                        id: cbParity
                        currentIndex: 2
                        model: ["Even", "Odd", "None", "Mark", "Space"]
                        Layout.preferredWidth: cbTestingComport.width
                    } // cbParity
                } // cllParity
                ColumnLayout {
                    id: cllStopBits
                    anchors.horizontalCenter: parent.horizontalCenter
                    Label {
                        id: lblStopBits
                        text: "Stop Bits"
                    } // lblStopBits
                    ComboBox {
                        id: cbStopBits
                        currentIndex: 0
                        model: [1, 1.5, 2]
                        Layout.preferredWidth: cbTestingComport.width
                    } // cbStopBits
                } // cllStopBits
                ColumnLayout {
                    id: cllFlowControl
                    anchors.horizontalCenter: parent.horizontalCenter
                    Label {
                        id: lblFlowControl
                        text: "Flow Control"
                    } // lblFlowControl
                    ComboBox {
                        id: cbFlowControl
                        currentIndex: 0
                        model: ["None", "On", "Off"]
                        Layout.preferredWidth: cbTestingComport.width
                    } // cbFlowControl
                } // cllFlowControl
                RowLayout {
                    id: rwlStartStopButtons
                    height: 40
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 20
                    Button {
                        id: btnStart
                        tooltip: qsTr("Start Port")
                        Layout.preferredHeight: 30
                        Layout.preferredWidth: 30
                        onClicked: {
                            if (sensorDataFeeds.sensorConfigurationModel.get_item_index("com_port", cbTestingComport.currentText) != -1) {
                                dlgOkay.message = "You selected an already used COM port, " +
                                                "please select another:\n\n" + cbTestingComport.currentText
                                dlgOkay.open()
                            } else {
                                btnStart.enabled = false
                                btnStop.enabled = true
                                toggleComPortSettings(false);
                                var com_port_dict = {
                                    "com_port": cbTestingComport.currentText,
                                    "baud_rate": parseInt(cbBaudRate.currentText),
                                    "data_bits": parseInt(cbDataBits.currentText),
                                    "parity": cbParity.currentText,
                                    "stop_bits": parseFloat(cbStopBits.currentText),
                                    "flow_control": cbFlowControl.currentText}
                                serialPortManager.add_thread(com_port_dict)
                                serialPortManager.start_thread(cbTestingComport.currentText)
                            }
                        }
                        style: enabled ? cvsStart : cvsStartDisabled
//                        style: ButtonStyle {
//                            label: Item {
//                                Canvas {
//                                    anchors.fill: parent
//                                    onPaint: {
//                                        var ctx = getContext("2d");
//                                        ctx.clearRect(0, 0, width, height)
//                                        ctx.fillStyle = "green";
//                                        ctx.beginPath();
//                                        ctx.moveTo(width/4, height/4);
//                                        ctx.lineTo(3*width/4, height/2);
//                                        ctx.lineTo(width/4, 3*height/4);
//                                        ctx.lineTo(width/4, height/4);
//                                        ctx.fill();
//                                    }
//                                }
//                            }
//                        }
                    } // btnStart
                    Button {
                        id: btnStop
                        tooltip: qsTr("Stop Port")
                        Layout.preferredHeight: 30
                        Layout.preferredWidth: 30
                        onClicked: {

                            btnStart.enabled = true
                            btnStop.enabled = false
                            toggleComPortSettings(true);

                            // Be sure that the com_port is not configured in the Operations displayMode
                            if (sensorDataFeeds.sensorConfigurationModel.get_item_index("com_port", cbTestingComport.currentText) == -1) {
                                serialPortManager.stop_thread(cbTestingComport.currentText)
                                serialPortManager.delete_thread(cbTestingComport.currentText)
                            }
                        }
                        enabled: false
                        style: enabled ? cvsStop : cvsStopDisabled
//                        style: ButtonStyle {
//                                label: Item {
//                                    Canvas {
//                                        anchors.fill: parent
//                                        onPaint: {
//                                            var ctx = getContext("2d");
//                                            ctx.clearRect(0, 0, width, height)
//                                            ctx.fillStyle = "red";
//                                            ctx.fillRect(width/4, height/4, width/2, height/2)
//                                            ctx.fill();
//                                        }
//                                    }
//                                }
//                            }
                    } // btnStop
                } // rwlStartStopButtons
                RowLayout {
                    id: rwlAddUpdateComPortButtons
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 20
                    Button {
                        id: btnAddPort
                        text: qsTr("Add Port")
                        onClicked: {
                            if (btnStart.enabled == false)
                                dlgAddComport.active_test_com_port = cbTestingComport.currentText;
                            else
                                dlgAddComport.active_test_com_port = "";

                            dlgAddComport.com_port = cbOperationsComport.currentText
                            dlgAddComport.baud_rate = parseInt(cbBaudRate.currentText)
                            dlgAddComport.data_bits = parseInt(cbDataBits.currentText)
                            dlgAddComport.parity = cbParity.currentText
                            dlgAddComport.stop_bits = parseFloat(cbStopBits.currentText)
                            dlgAddComport.flow_control = cbFlowControl.currentText
                            dlgAddComport.open()
                        }
                    } // btnAddPort
                    Button {
                        id: btnUpdatePort
                        text: qsTr("Update Port")
                        enabled: false
                        onClicked: {

                            /* Logic as follows.  Need to compare two com_port values:

                                cbOperationsComport.currentText
                                tvSensorConfiguration.model.get(tvSensorConfiguration.currentRow).com_port

                            */

                            var com_port = cbOperationsComport.currentText;
                            var row = tvSensorConfiguration.currentRow;
                            var configured_com_port = (row != -1) ? tvSensorConfiguration.model.get(row).com_port : "";

                            var update_ok = false;
                            if (configured_com_port == com_port) {
                                // Great, just updating the currently selected com_port other variables
                                update_ok = true;

                            } else {
                                var index = sensorDataFeeds.sensorConfigurationModel.get_item_index("com_port", com_port);
                                if (index == -1) {
                                    if (cbTestingComport.currentText != com_port)
                                        update_ok = true;
                                    else if ((cbTestingComport.currentText == com_port) & (btnStart.enabled))
                                        update_ok = true;
                                } else if (index == row)
                                    update_ok = true;
                            }

                            if (update_ok) {
                                if (tvSensorConfiguration.currentRow != -1) {
                                    var deployed_equipment_id = sensorDataFeeds.sensorConfigurationModel.
                                        get(tvSensorConfiguration.currentRow).deployed_equipment_id
                                    var item = {
                                        "deployed_equipment_id": deployed_equipment_id,
                                        "com_port": cbOperationsComport.currentText,
                                        "baud_rate": parseInt(cbBaudRate.currentText),
                                        "data_bits": parseInt(cbDataBits.currentText),
                                        "parity": cbParity.currentText,
                                        "stop_bits": parseFloat(cbStopBits.currentText),
                                        "flow_control": cbFlowControl.currentText
                                    }
                                    sensorDataFeeds.sensorConfigurationModel.update_row(item);
                                }
                            } else {
                                dlgOkay.message = "You selected an already used COM port, " +
                                                "please select another:\n\n" + com_port
                                dlgOkay.open()
                            }
                        }
                    } // btnUpdatePort
                } // rwlAddUpdateComPortButtons
            } // cllComportSettings

        } // leftPanel
        Rectangle {
            id: rightPanel
            Layout.fillWidth: true
            color: SystemPaletteSingleton.window(true)

            ColumnLayout {
                id: cllRightPanel
                spacing: 10

                // Testing displayMode
                TableView {
                    id: tvTestSentences
                    Layout.preferredWidth: rightPanel.width
                    Layout.preferredHeight: rightPanel.height
                    selectionMode: SelectionMode.SingleSelection
                    visible: false
                    headerVisible: false
                    model: sensorDataFeeds.testSentencesModel
                    TableViewColumn {
                        role: "sentence"
                        title: ""
                        width: rightPanel.width
                    } // sentence
                } // tvTestSentences

                // Operations displayModes
                TableView {
                    id: tvRawSentences
                    Layout.preferredWidth: rightPanel.width
                    Layout.preferredHeight: rightPanel.height
                    selectionMode: SelectionMode.SingleSelection
                    visible: false
                    headerVisible: false
                    model: sensorDataFeeds.rawSentencesModel
                    TableViewColumn {
                        role: "sentence"
                        title: ""
                        width: rightPanel.width
                    } // sentence
                } // tvRawSentences
                TableView {
                    id: tvErrorMessages
                    Layout.preferredWidth: rightPanel.width
                    Layout.preferredHeight: 300
                    selectionMode: SelectionMode.SingleSelection
                    visible: false
                    model: sensorDataFeeds.errorMessagesModel
                    TableViewColumn {
                        id: tvcDateTime
                        role: "date_time"
                        title: "Date / Time"
                        width: 110
                    } // date_time
                    TableViewColumn {
                        id: tvcComPort
                        role: "com_port"
                        title: "COM Port"
                        width: 60
                    } // date_time
                    TableViewColumn {
                        id: tvcMessage
                        role: "message"
                        title: "Problem"
                        width: 150
                    } // message
                    TableViewColumn {
                        id: tvcResolution
                        role: "resolution"
                        title: "Resolution"
                        width: 235
                    } // resolution
                    TableViewColumn {
                        role: "exception"
                        title: "Exception Message"
                        width: rightPanel.width - tvcDateTime.width -
                            tvcComPort.width - tvcMessage.width - tvcResolution.width - 3
                    } // exception
                } // tvErrorMessages

                // Measurement displayMode
                TableView {
                    id: tvParsedSentences
                    Layout.preferredWidth: rightPanel.width
                    Layout.preferredHeight: 200
                    highlightOnFocus: false
                    property int currentColumn: 0
                    selectionMode: SelectionMode.SingleSelection
                    visible: false

                    TableViewColumn {
                        role: "column1"
                        title: "1"
                        width: 60
                    } // column1
                    TableViewColumn {
                        role: "column2"
                        title: "2"
                        width: 60
                    } // column2
                    TableViewColumn {
                        role: "column3"
                        title: "3"
                        width: 60
                    } // column3
                    TableViewColumn {
                        role: "column4"
                        title: "4"
                        width: 60
                    } // column4
                    TableViewColumn {
                        role: "column5"
                        title: "5"
                        width: 60
                    } // column5
                    TableViewColumn {
                        role: "column6"
                        title: "6"
                        width: 60
                    } // column6
                    TableViewColumn {
                        role: "column7"
                        title: "7"
                        width: 60
                    } // column7
                    TableViewColumn {
                        role: "column8"
                        title: "8"
                        width: 60
                    } // column8
                    TableViewColumn {
                        role: "column9"
                        title: "9"
                        width: 60
                    } // column9
                    TableViewColumn {
                        role: "column10"
                        title: "10"
                        width: 60
                    } // column10
                    TableViewColumn {
                        role: "column11"
                        title: "11"
                        width: 60
                    } // column11
                    TableViewColumn {
                        role: "column12"
                        title: "12"
                        width: 60
                    } // column12

                    model: sensorDataFeeds.parsedSentencesModel

                    style: TableViewStyle {
                        itemDelegate: Rectangle {
                            color: {
                                var bgColor;
                                if (model != null) {
                                    bgColor = model.index % 2 ? "white" : "whitesmoke";
                                } else {
                                    bgColor = styleData.row %2 ? "white" : "whitesmoke";
                                }
                                var activeRow = tvParsedSentences.currentRow === styleData.row
                                var activeColumn = tvParsedSentences.currentColumn === styleData.column
                                activeRow && activeColumn ? "skyblue" : bgColor
                            }
                            Text {
                                text: styleData.value ? styleData.value : ""
                                elide: Text.ElideRight
//                                color: textColor
                                color: {
                                    var activeRow = tvParsedSentences.currentRow === styleData.row
                                    var activeColumn = tvParsedSentences.currentColumn === styleData.column
                                    activeRow && activeColumn ? "white" : "black"
                                }
                                renderType: Text.NativeRendering
                                font.pixelSize: 11
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    tvParsedSentences.currentRow = styleData.row
                                    tvParsedSentences.currentColumn = styleData.column
                                    model.currentIndex = styleData.row
                                    if (tfSubstr.text == "")
                                        tfSentence.text = tvParsedSentences.model.get(styleData.row).column1;
                                    tfField.text = styleData.column + 1;
//                                    parent.forceActiveFocus()
                                }
                            }
                        }
                    }
                } // tvParsedSentences
                GridLayout {
                    id: glMatchingData
                    columns: 5
                    rows: 2
                    columnSpacing: 20
                    rowSpacing: 10
                    anchors.horizontalCenter: tvParsedSentences.horizontalCenter

                    Label {
                        id: lblEquipment
                        text: qsTr("Equipment")
                    } // lblEquipment
                    RowLayout {
                        id: rwlLineStart
                        Label {
                            id: lblSentence
                            text: qsTr("Sentence")
                        } // lblSentence
                        TextField {
                            id: tfSubstr
                            text: qsTr("")
                            placeholderText: qsTr("Substr")
                            Layout.preferredWidth: 50
                            onTextChanged: {
                                tvParsedSentences.model.clear()
                                tfSentence.text = text
                            }
                        } // tfSubstr
                    } // rwlLineStart
                    Label {
                        id: lblField
                        text: qsTr("Field")
                    } // lblField
                    Label {
                        id: lblLineEnding
                        text: qsTr("Line Ending")
                    } // lblLineEnding
                    RowLayout {
                        id: rwlMeasurement
                        spacing: 10
                        Label {
                            id: lblMeasurement
                            text: qsTr("Measurement")
                        } // lblMeasurement
                        Button {
                            id: btnAddMeasurement
                            Layout.preferredHeight: 25
                            Layout.preferredWidth: 25
                            onClicked: {
                                dlgNewMeasurement.open()
                            }
                            style: ButtonStyle {
                                label: Item {
                                    Canvas {
                                        anchors.fill: parent
                                        onPaint: {
                                            var ctx = getContext("2d");
                                            ctx.lineWidth = 3;
                                            ctx.strokeStyle = Qt.rgba(0, 0, 0, 1);
                                            ctx.beginPath();
                                            ctx.moveTo(width/2, height/4);
                                            ctx.lineTo(width/2, 3*height/4);
                                            ctx.stroke();
                                            ctx.beginPath();
                                            ctx.moveTo(width/4, height/2);
                                            ctx.lineTo(3*width/4, height/2);
                                            ctx.stroke();
                                        }
                                    }
                                }
                            }
                        } // btnAddMeasurement

                    } // rwlMeasurement
                    TextField {
                        id: tfEquipment
                        text: qsTr("")
                    } // tfEquipment
                    TextField {
                        id: tfSentence
                        text: qsTr("")
                        Layout.preferredWidth: 100
                    } // tfSentence
                    TextField {
                        id: tfField
                        text: qsTr("")
                        Layout.preferredWidth: 40
                    } // tfField
                    Button {
                        id: btnLineEnding
                        text: "\\r\\n"
                        Layout.preferredWidth: 70
                        onClicked: {
                            dlgLineEnding.tfLineEnding.text = text;
                            dlgLineEnding.lastCharacters = ["\\r", "?", "\\n", "?"];
                            dlgLineEnding.open()
                        }
                    } // btnLineEnding

                    ComboBox {
                        id: cbMeasurement
//                        model: (Array.apply(0, Array(250)).map(function (x,y) {return y+1})).map(String)
                        model: sensorDataFeeds.measurementsUnitsOfMeasurementModel
                        currentIndex: 0
                        Layout.preferredWidth: 200
                    } // cbMeasurement

                } // glMatchingData
                RowLayout {
                    id: rwlModifyMatchings
                    anchors.horizontalCenter: tvParsedSentences.horizontalCenter
                    anchors.top: glMatchingData.bottom
                    anchors.topMargin: 20
                    Button {
                        id: btnAdd
                        text: qsTr("Add")
                        onClicked: {
                            var item = createMatchingItem("add");
                            if (item != null) {
                                sensorDataFeeds.measurementConfigurationModel.add_row(item);
                            }
                        }
                    } // btnAdd
                    Button {
                        id: btnUpdate
                        text: qsTr("Update")
                        onClicked: {
                            var item = createMatchingItem("update");
                            if ((item != null) & (tvMatchings.currentRow != -1)) {
                                sensorDataFeeds.measurementConfigurationModel.update_row(item);
                            }
                        }
                    } // btnUpdate
                    Button {
                        id: btnDelete
                        text: qsTr("Delete")
                        onClicked: {
                            var row = tvMatchings.currentRow;
                            if ((tvMatchings.selection.count > 0) & (row != -1)) {
                                var id = tvMatchings.model.get(row).parsing_rules_id
                                sensorDataFeeds.measurementConfigurationModel.delete_row(id)
                                tvMatchings.selection.clear();
                            }
                        }
                    } // btnDelete

                } // rwlModifyMatchings
                TableView {
                    id: tvMatchings
                    anchors.horizontalCenter: tvParsedSentences.horizontalCenter
                    anchors.top: rwlModifyMatchings.bottom
                    anchors.topMargin: 20
                    Layout.preferredWidth: 500
                    Layout.preferredHeight: 300
                    property int currentColumn: 0
                    selectionMode: SelectionMode.SingleSelection
                    horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

                    TableViewColumn {
                        role: "equipment"
                        title: "Equipment"
                        width: 100
                    } // equipment
                    TableViewColumn {
                        role: "line_starting"
                        title: "Sentence"
                        width: 80
                    } // line_starting
                    TableViewColumn {
                        role: "field_position"
                        title: "Field"
                        width: 40
                    } // field_position
                    TableViewColumn {
                        role: "line_ending"
                        title: "Line Ending"
                        width: 80
                    } // line_ending
                    TableViewColumn {
                        role: "measurement"
                        title: "Measurement"
                        width: 200
                    } // measurement

                    model: sensorDataFeeds.measurementConfigurationModel

                    selection.onSelectionChanged: {
                        var status = (selection.count == 0) ? false: true
                        btnUpdate.enabled = status;
                        btnDelete.enabled = status;
                    }
                    onFocusChanged: {
                        var status = focus ? (selection.count > 0 ? true : false) : false
                        btnUpdate.enabled = status;
                        btnDelete.enabled = status;
                    }

                } // tvMatchings
                ColumnLayout {
                    id: cllReorderButtons
                    anchors.verticalCenter: tvMatchings.verticalCenter
                    anchors.left: tvMatchings.right
                    anchors.leftMargin: 10
                    enabled: false
                    Button {
                        id: btnMoveUp
                        Layout.preferredHeight: 25
                        Layout.preferredWidth: 25
                        onClicked: {
    //                        messageDialog.show('clicked started')
                        }
                        style: ButtonStyle {
                            label: Item {
                                Canvas {
                                    anchors.fill: parent
                                    onPaint: {
                                        var ctx = getContext("2d");
                                        ctx.clearRect(0, 0, width, height)
                                        ctx.fillStyle = "black";
                                        ctx.beginPath();
                                        ctx.moveTo(width/4, 3*height/4);
                                        ctx.lineTo(width/2, height/4);
                                        ctx.lineTo(3*width/4, 3*height/4);
                                        ctx.lineTo(width/4, 3*height/4);
                                        ctx.fill();
                                    }
                                }
                            }
                        }
                    } // btnMoveUp
                    Button {
                        id: btnMoveDown
                        Layout.preferredHeight: 25
                        Layout.preferredWidth: 25
                        onClicked: {
    //                        messageDialog.show('clicked started')
                        }
                        style: ButtonStyle {
                            label: Item {
                                Canvas {
                                    anchors.fill: parent
                                    onPaint: {
                                        var ctx = getContext("2d");
                                        ctx.clearRect(0, 0, width, height)
                                        ctx.fillStyle = "black";
                                        ctx.beginPath();
                                        ctx.moveTo(width/4, height/4);
                                        ctx.lineTo(3*width/4, height/4);
                                        ctx.lineTo(width/2, 3*height/4);
                                        ctx.lineTo(width/4, height/4);
                                        ctx.fill();
                                    }
                                }
                            }
                        }
                    } // btnMoveDown
                } // cllReorderButtons

            } // cllRightPanel
        } // rightPanel
    }

    NewMeasurementDialog {
        id: dlgNewMeasurement
        onRejected: {
//            resetfocus()
        }
        onAccepted: {

//            resetfocus()
//            tfSetId.text = this.tfYear.text +
//                this.cbSamplingType.model.get(this.cbSamplingType.currentIndex)["sampling_type_number"] +
//                this.cbVesselNumber.model.get(this.cbVesselNumber.currentIndex)["vessel_number"] +
//                this.tfId.text
        }
    }
    AddComportDialog { id: dlgAddComport }
    OkayDialog { id: dlgOkay }
    LineEndingDialog {
        id: dlgLineEnding
        onAccepted: {
            btnLineEnding.text = tfLineEnding.text
        }
    }
    ToolTip {
        id: ttSubstr
        width: 200
        target: tfSubstr
        text: qsTr("Enter text to identify a substring of\nthe first field as the sentence type.\n\nLeave blank to specify the whole first\nfield")
    } // ttSubstr

//    states: [
//        State {
//            name: "testing_active"
//            PropertyChanges { target: btnStart; enabled: false}
//            PropertyChanges { target: btnStop; enabled: true}
//            PropertyChanges { target: cbTestingComport; enabled: false}
//            PropertyChanges { target: cbBaudRate; enabled: false}
//            PropertyChanges { target: cbDataBits; enabled: false}
//            PropertyChanges { target: cbParity; enabled: false}
//            PropertyChanges { target: cbStopBits; enabled: false}
//            PropertyChanges { target: cbFlowControl; enabled: false}
//        }, // testing_active
//        State {
//            name: "testing_inactive"
//            PropertyChanges { target: btnStart; enabled: true}
//            PropertyChanges { target: btnStop; enabled: false}
//            PropertyChanges { target: cbTestingComport; enabled: true}
//            PropertyChanges { target: cbBaudRate; enabled: true}
//            PropertyChanges { target: cbDataBits; enabled: true}
//            PropertyChanges { target: cbParity; enabled: true}
//            PropertyChanges { target: cbStopBits; enabled: true}
//            PropertyChanges { target: cbFlowControl; enabled: true}
//        } // testing_inactive
//    ]

}

