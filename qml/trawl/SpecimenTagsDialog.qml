import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../common"

Dialog {
    id: dlg
    width: 640
    height: 800
//    modality: dialogModal.checked ? Qt.WindowModal : Qt.NonModal
    title: "Specimen Tags Review"
//    title: customizeTitle.checked ? windowTitleField.text : "Customized content"

//    property string linealType: "length"
//    property real linealValue
//    property real weight
//    property int age

    property string message: "Specimen Tags Review"
//    property string action: "Do you wish to proceed?"
    property string accepted_action: ""

    property alias btnOkay: btnOkay
//    standardButtons: StandardButton.Ok | StandardButton.Cancel

    onRejected: {}
    onAccepted: {}
//    onButtonClicked: { console.info("onButtonClicked") }

    Component.onCompleted: {
        selectSpecimenType("ovary")
    }

    function selectSpecimenType(type) {
        fishSampling.SpecimenTagsModel.populate_tags(type)
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"
        Label {
            id: lblMessage
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            y: 20
            text: message
            font.pixelSize: 20
        } // lblMessage
        ColumnLayout {
            id: cllFilters
            x: 10
            anchors.verticalCenter: parent.verticalCenter
            Label {
                id: lblFilter
                text: "Filters"
                font.family: "Helvetica"
                font.pixelSize: 20
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
            }
            TrawlBackdeckButton {
                id: btnOvaries
                text: qsTr("Ovaries")
                checkable: true
                checked: true
                exclusiveGroup: egFilters
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: {
                    selectSpecimenType("ovary")
                }
            }
            TrawlBackdeckButton {
                id: btnStomachs
                text: qsTr("Stomachs")
                checkable: true
                exclusiveGroup: egFilters
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: {
                    selectSpecimenType("stomach")
                }
            }
            TrawlBackdeckButton {
                id: btnTissues
                text: qsTr("Tissues")
                checkable: true
                exclusiveGroup: egFilters
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: {
                    selectSpecimenType("tissue")
                }
            }
            TrawlBackdeckButton {
                id: btnFinclips
                text: qsTr("Finclips")
                checkable: true
                exclusiveGroup: egFilters
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: {
                    selectSpecimenType("finclip")
                }
            }
            TrawlBackdeckButton {
                id: btnWholeSpecimen
                text: qsTr("Whole\nSpecimen")
                checkable: true
                exclusiveGroup: egFilters
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: {
                    selectSpecimenType("whole specimen")
                }
            }
        } // cllFilters
        TrawlBackdeckTableView {
            id: tvTags
            anchors.left: cllFilters.right
            anchors.leftMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - cllFilters.width - 40
            height: parent.height - lblMessage.height - rwlButtons.height - 100
            selectionMode: SelectionMode.SingleSelection
            headerVisible: true
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

            model: fishSampling.SpecimenTagsModel

            TableViewColumn {
                role: "tag"
                title: "Tag Number"
                width: tvTags.width * 0.55
            }
            TableViewColumn {
                role: "specimenNumber"
                title: "Specimen Number"
                width: tvTags.width * 0.45
            }
        }
        ExclusiveGroup {
            id: egFilters
        }

        RowLayout {
            id: rwlButtons
            anchors.horizontalCenter: parent.horizontalCenter
            y: dlg.height - this.height - 20
            spacing: 20
            TrawlBackdeckButton {
                id: btnOkay
                text: "Okay"
                Layout.preferredWidth: this.width
                Layout.preferredHeight: this.height
                onClicked: { dlg.accept() }
            } // btnOkay
        } // rwlButtons

//        Keys.onPressed: if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) dlg.click(StandardButton.Retry)
        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject() // especially necessary on Android
    }
}
