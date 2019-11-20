import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0

import "../common"

Item {

    Component.onDestruction: {
        tbdSM.to_home_state()
    }

    Component.onCompleted: {
        equipmentSelectionChanged()
    }

    Connections {
        target: tvSerialPorts.selection
        onSelectionChanged: serialPortSelectionChanged();
    } // onSelectionChanged

    Connections {
        target: cbEquipment
        onCurrentIndexChanged: equipmentSelectionChanged();
    }

    Component {
        id: cvsPlay
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "black";
                ctx.beginPath();
                ctx.moveTo(width/4, height/4);
                ctx.lineTo(3*width/4, height/2);
                ctx.lineTo(width/4, 3*height/4);
                ctx.lineTo(width/4, height/4);
                ctx.fill();
            }
        }
    } // cvsPlay
    Component {
        id: cvsStop
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "black";
                ctx.fillRect(width/4, height/4, width/2, height/2)
                ctx.fill();
            }
        }
    } // cvsStop
    Component {
        id: cvsMeatball
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = statusColor
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatball
    Component {
        id: cvsMeatballGreen
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "#28FF28" // "lightgreen"
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
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatballYellow
    Component {
        id: cvsMeatballBlack
        Canvas {
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height)
                ctx.fillStyle = "black"
                ctx.ellipse(width/6,height/6, 2*width/3, 2*height/3)
                ctx.fill();
            }
        }
    } // cvsMeatballBlack

    function equipmentSelectionChanged() {

        // Update the measurementsModel
        if (cbEquipment.currentIndex != -1) {
//            console.info('equipmentId: ' + cbEquipment.model.get(cbEquipment.currentIndex)["equipmentId"])
            serialPortManager.measurementsModel = cbEquipment.model.get(cbEquipment.currentIndex)["equipmentId"]
        } else {
            serialPortManager.measurementsModel = null
        }

    }

    function serialPortSelectionChanged() {

        tvSerialPorts.selection.forEach(
            function(idx) {
                var item = tvSerialPorts.model.get(idx)

                cbComPort.currentIndex = cbComPort.find(item["serialPort"].toString())

                var equipmentName = item["equipmentName"].toString()
                var pattern = /\(Printer \d\)/;
                if (equipmentName.indexOf("(Printer") != -1) {
                    equipmentName = equipmentName.replace(pattern, "").trim()
                }
                cbEquipment.currentIndex = cbEquipment.find(equipmentName)

                cbBaudRate.currentIndex = cbBaudRate.find(item["baudRate"].toString())
                cbDataBits.currentIndex = cbDataBits.find(item["dataBits"].toString())
                cbParity.currentIndex = cbParity.find(item["parity"].toString())
                cbStopBits.currentIndex = cbStopBits.find(item["stopBits"].toString())
                cbFlowControl.currentIndex = cbFlowControl.find(item["flowControl"].toString())
                cbMeasurement.currentIndex = item["measurementName"] ?
                    cbMeasurement.find(item["measurementName"].toString()) : cbMeasurement.find("None")

                if (item["readerOrWriter"].toLowerCase() == "reader") {
                    btnTogglePort.state = qsTr("enabled")
                    if (item["playControl"] == "stop")
                        btnTogglePort.text = "Stop\nPort"
                    else
                        btnTogglePort.text = "Start\nPort"
                } else {
                    btnTogglePort.state = qsTr("disabled")
                }
            }
        )

        if (tvSerialPorts.selection.count == 0) {
            btnUpdatePort.state = qsTr("disabled")
//            btnDeletePort.state = qsTr("disabled")
//            btnTogglePort.state = qsTr("disabled")
        } else {
            btnUpdatePort.state = qsTr("enabled")
//            btnDeletePort.state = qsTr("enabled")
//            btnTogglePort.state = qsTr("enabled")
        }
    }

    function getMeatball(index, status) {

        if (index < 0)
            return cvsMeatballBlack
        var item = tvSerialPorts.model.get(index)
        var serialPort = item["serialPort"]
        serialPortManager.requestedPort = serialPort
        switch (serialPortManager.portStatus) {
            case "red": return cvsMeatballRed
            case "yellow": return cvsMeatballYellow
            case "green": return cvsMeatballGreen
        }
    }

    function getPlayControlIcon(index, status) {
        if (index < 0)
            return cvsPlay
        var item = tvSerialPorts.model.get(index)
        var serialPort = item["serialPort"]
        serialPortManager.requestedPort = serialPort
        switch (serialPortManager.playStatus) {
            case "play": return cvsPlay
            case "stop": return cvsStop
        }
    }

    TrawlBackdeckTableView {
        id: tvSerialPorts
        x: 20
        y: 20
        width: 420
        height: 330
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        verticalScrollBarPolicy: Qt.ScrollBarAsNeeded

        model: serialPortManager.serialPortsModel

        TableViewColumn {
            role: "dataStatus"
            title: ""
            width: 30

            delegate: Component {
                Loader {
                    anchors.fill: parent
                    sourceComponent: styleData.row >= 0 ? getMeatball(styleData.row, serialPortManager.portStatus) : cvsMeatballBlack
                }
            }
        } // dataStatus
        TableViewColumn {
            role: "serialPort"
            title: "COM"
            width: 60
            delegate: Text {
                text: styleData.value ? styleData.value : ""  //styleData.value.toFixed(3)
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        } // serialPort
        TableViewColumn {
            role: "equipmentName"
            title: "Equipment"
            width: 300
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // equipmentName
        TableViewColumn {
            role: "playControl"
            title: ""
            width: 30
            delegate: Component {
                Loader {
                    anchors.fill: parent
                    sourceComponent: styleData.row >= 0 ? getPlayControlIcon(styleData.row, serialPortManager.playStatus) : cvsMeatballBlack
                }
            }
        } // playControl

    } // tvSerialPorts

    ColumnLayout {
        id: clSerialSettings
        x: tvSerialPorts.x
        y: tvSerialPorts.y + tvSerialPorts.height + 10
        spacing: 20

        RowLayout {
            spacing: 20
            ColumnLayout {
                Label {
                    id: lblComPort
                    text: qsTr("COM Port")
                    font.pixelSize: 20
                }
                FramComboBox {
                    id: cbComPort

                    // TypeError: Cannot read property of null - when the ComboBox has to be scrolled...why?
                    model: (Array.apply(0, Array(250)).map(function (x,y) {return y+1})).map(String)
                    currentIndex: -1
                    Layout.preferredWidth: 100
                }
            } // comPort
            ColumnLayout {
                Label {
                    id: lblEquipment
                    text: qsTr("Equipment")
                    font.pixelSize: 20
                }
                FramComboBox {
                    id: cbEquipment
                    model: serialPortManager.equipmentModel
                    currentIndex: -1
                    Layout.preferredWidth: 300
                }
            } // equipment
        }
        RowLayout {
            spacing: 20

            ColumnLayout {
                Label {
                    id: lblBaudRate
                    text: qsTr("Baud Rate")
                    font.pixelSize: 20
                }
                FramComboBox {
                    id: cbBaudRate
                    model: [ "1200", "2400", "4800", "9600", "19200", "57600"]
                    currentIndex: 3
                    Layout.preferredWidth: 100
                }
            } // baudRate
            ColumnLayout {
                Label {
                    id: lblMeasurement
                    text: qsTr("Measurement")
                    font.pixelSize: 20
                }
                FramComboBox {
                    id: cbMeasurement
                    model: serialPortManager.measurementsModel
                    currentIndex: -1
                    Layout.preferredWidth: 300
                }
            } // measurement
        }
        RowLayout {
            spacing: 20

            ColumnLayout {
                Label {
                    id: lblParity
                    text: qsTr("Parity")
                    font.pixelSize: 20
                }
                FramComboBox {
                    id: cbParity
                    model: [ "None", "Even", "Odd", "Mark", "Space"]
                    currentIndex: 0
                    Layout.preferredWidth: 100
                }
            } // parity
            ColumnLayout {
                Label {
                    id: lblDataBits
                    text: qsTr("Data Bits")
                    font.pixelSize: 20
                }
                FramComboBox {
                    id: cbDataBits
                    model: [ "5", "6", "7", "8"]
                    currentIndex: 3
                    Layout.preferredWidth: 80
                }
            } // dataBits
            ColumnLayout {
                Label {
                    id: lblStopBits
                    text: qsTr("Stop Bits")
                    font.pixelSize: 20
                }
                FramComboBox {
                    id: cbStopBits
                    model: [ "1", "1.5", "2"]
                    currentIndex: 0
                    Layout.preferredWidth: 80
                }
            } // stopBits
            ColumnLayout {
                Label {
                    id: lblFlowControl
                    text: qsTr("Flow Control")
                    font.pixelSize: 20
                }
                FramComboBox {
                    id: cbFlowControl
                    model: [ "None", "On", "Off"]
                    currentIndex: 0
                    Layout.preferredWidth: 100
                }
            } // flowControl
        }
    } // clSerialSettings

    RowLayout {
        id: rlSerialButtons
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        x: clSerialSettings.x
        spacing: 10
        TrawlBackdeckButton {
            id: btnUpdatePort
            text: qsTr("Update\nPort")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            state: qsTr("disabled")
            onClicked: {
                if (tvSerialPorts.currentRow == -1) return;

                var data = {}
                var index
                var equipmentLabel
                tvSerialPorts.selection.forEach(
                    function(idx) {
                        index = idx
                        var item = tvSerialPorts.model.get(idx)
                        data["deployedEquipmentId"] = item["deployedEquipmentId"]
                        data["dataStatus"] = item["dataStatus"]
                        data["playControl"] = item["playControl"]
                        equipmentLabel = item["equipmentName"]
                    }
                )
                data["serialPort"] = parseInt(cbComPort.currentText)
                data["baudRate"] = parseInt(cbBaudRate.currentText)
                data["dataBits"] = parseInt(cbDataBits.currentText)
                data["parity"] = cbParity.currentText
                data["stopBits"] = parseFloat(cbStopBits.currentText)
                data["flowControl"] = cbFlowControl.currentText

                data["measurementTypeId"] = cbMeasurement.model.get(cbMeasurement.currentIndex)["measurementTypeId"]
                data["measurementName"] = cbMeasurement.model.get(cbMeasurement.currentIndex)["measurementName"]
                data["equipmentId"] = cbEquipment.model.get(cbEquipment.currentIndex)["equipmentId"]
                data["equipmentName"] = cbEquipment.model.get(cbEquipment.currentIndex)["equipmentName"]

                if (data["equipmentName"].indexOf("Printer") != -1) {
                    data["equipmentName"] = equipmentLabel
                }


                serialPortManager.update_port(index, data)
            }
        }
        TrawlBackdeckButton {
            id: btnDeletePort
            text: qsTr("Delete\nPort")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            state: qsTr("disabled")
            onClicked: { }
        }
        TrawlBackdeckButton {
            id: btnAddPort
            text: qsTr("Add New\nPort")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            state: qsTr("disabled")
            onClicked: { }
        }
    } // rlSerialButtons

    TrawlBackdeckTableView {
        id: tvMessages
        anchors.left: tvSerialPorts.right
        anchors.leftMargin: 40
        y: 20
        width: parent.width - tvSerialPorts.width - 80
        height: parent.height - rlFinalButtons.height - 60
        selectionMode: SelectionMode.SingleSelection
        headerVisible: true
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
        verticalScrollBarPolicy: Qt.ScrollBarAsNeeded

        model: serialPortManager.messagesModel

        property string selectedComPort: "COM4"

        TableViewColumn {
            role: "sentence"
            title: "Sentence"
            width: 250
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
            }
        } // sentence
        TableViewColumn {
            role: "measurement"
            title: "Measurement"
            width: 150
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
            }
        } // measurement
        TableViewColumn {
            role: "value"
            title: "Value"
            width: 100
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
            }
        } // value
    }

    RowLayout {
        id: rlFinalButtons
        x: main.width - this.width - 20
        y: main.height - this.height - 20
        spacing: 10

        TrawlBackdeckButton {
            id: btnClearMessages
            text: qsTr("Clear\nMessages")
            state: qsTr("enabled")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                tvMessages.model.clear()
            }
        } // btnClearMessages
        TrawlBackdeckButton {
            id: btnTogglePort
            text: qsTr("Stop\nPort")
            state: qsTr("disabled")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                var serialPort
                tvSerialPorts.selection.forEach(
                    function(idx) {
                        var item = tvSerialPorts.model.get(idx)
                        serialPort = parseInt(item["serialPort"])
                    }
                )
                if (this.text.indexOf("Start") > -1) {
                    serialPortManager.start_thread(serialPort)
                    this.text = "Stop\nPort"
                } else {
                    serialPortManager.stop_thread(serialPort)
                    this.text = "Start\nPort"
                }
            }
        } // btnTogglePort
        TrawlBackdeckButton {
            id: btnToggleAllPorts
            text: qsTr("Stop\nAll Ports")
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            onClicked: {
                var status
                if (this.text.indexOf("Start") > -1) {
                    status = "stop"
                    serialPortManager.start_all_threads()
                    this.text = "Stop\nAll Ports"
                } else {
                    status = "play"
                    serialPortManager.stop_all_threads()
                    this.text = "Start\nAll Ports"
                }
                for (var i=0; i < tvSerialPorts.model.items.length; i++) {
                    tvSerialPorts.model.get(i)["playControl"] = status
                }
                tvSerialPorts.selection.forEach(
                    function(idx) {
                        if (status == "stop")
                            btnTogglePort.text = "Stop\nPort"
                        else
                            btnTogglePort.text = "Start\nPort"
                    }
                )

            }
        } // btnToggleAllPorts
        TrawlBackdeckButton {
            id: btnNotes
            text: qsTr("Note")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: {
                dlgNote.reset(tvSerialPorts)
                dlgNote.open()
            }
        } // btnNotes

        TrawlBackdeckButton {
            id: btnDone
            text: qsTr("<<")
            Layout.preferredWidth: 60
            Layout.preferredHeight: this.height
            onClicked: screens.pop()
        } // btnDone
    } // rlFinalButtons

    TrawlNoteDialog { id: dlgNote }

}