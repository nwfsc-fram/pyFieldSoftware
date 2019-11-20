import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Window 2.2

import "../common"

Item {
    id: root

    ColumnLayout {
        id: clFishSampling
        spacing: 20
        anchors.fill: parent

        RowLayout {
            id: rlTopButtons
            spacing: 10
            anchors.top: parent.top
            anchors.topMargin: 10
            anchors.left: parent.left
            BackdeckButton {
                id: btnHome
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("<<")
                onClicked: {
                    screens.pop();
                }
            } // btnHome

            Label { Layout.preferredWidth: 100 }
            BackdeckButton {
                id: btnAddFish
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Add Fish")
                onClicked: {
                    dlgFishSamplingEntry.open()
                }
            } // btnAddFish
            BackdeckButton {
                id: btnEditFish
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Edit Fish")
            } // btnEditFish
            BackdeckButton {
                id: btnDeleteFish
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Delete Fish")
            } // btnDeleteFish

            Label { Layout.fillWidth: true }

            BackdeckButton {
                id: btnValidate
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Finished &\nValidate")
            } // btnNotes
            BackdeckButton {
                id: btnNotes
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Note")
                onClicked: {
                    dlgNote.reset()
                    dlgNote.open()
                }
            } // btnNotes

        } // rlTopButtons

        BackdeckTableView {
            id: tvSpecimens
            Layout.preferredWidth: parent.width
            Layout.fillHeight: true
            selectionMode: SelectionMode.SingleSelection
            headerVisible: true
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

//            model: fishSampling.model
            model: ListModel {
                ListElement {
                    parentSpecimenNumber: 1
                    species: "Bocaccio"
                    adh: "A31"
                    weight: 5.100
                    linealValue: 031
                    sex: "M"
                    ageNumber: 123445098
                    finclip: 312
                    special: "O,S,T,OV,GV"
                    disposition: "S"
                }
                ListElement {
                    parentSpecimenNumber: 2
                    species: "Vermillion"
                    adh: "B12"
                    weight: 5.100
                    linealValue: 022
                    sex: "F"
                    ageNumber: 123443422
                    finclip: 314
                    special: "N"
                    disposition: "S"
                }
                ListElement {
                    parentSpecimenNumber: 3
                    species: "California Market Squid"
                    adh: "C44"
                    weight: 5.100
                    linealValue: 031
                    sex: "M"
                    ageNumber: 123445098
                    finclip: 312
                    special: "Y"
                    disposition: "R"
                }
            }

            TableViewColumn {
                role: "parentSpecimenNumber"
                title: "ID"
                width: 60
            } // parentSpecimenNumber
            TableViewColumn {
                role: "species"
                title: "Species"
                width: 220
            } // species
            TableViewColumn {
                role: "adh"
                title: "A-D-H"
                width: 80
            } // adh
            TableViewColumn {
                role: "weight"
                title: "Weight"
                width: 80
                delegate: Text {
                    text: (typeof styleData.value == 'number') ? styleData.value.toFixed(2) : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // weight
            TableViewColumn {
                role: "linealValue"
                title: "Len"
                width: 60
                delegate: Text {
                    text: (typeof styleData.value == 'number') ? styleData.value.toFixed(0) : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // linealValue
            TableViewColumn {
                role: "sex"
                title: "Sex"
                width: 60
            } // sex
            TableViewColumn {
                role: "ageNumber"
                title: "Otolith"
                width: 120
                delegate: Text {
                    text: (typeof styleData.value == 'number') ? styleData.value : ""
                    font.pixelSize: 20
                    verticalAlignment: Text.AlignVCenter
                }
            } // ageNumber
            TableViewColumn {
                role: "finclip"
                title: "Finclip"
                width: 80
            } // finclip
            TableViewColumn {
                role: "special"
                title: "Special"
                width: 200
            } // special
            TableViewColumn {
                role: "disposition"
                title: "Dis"
                width: 50
            } // disposition
        } // tvSpecimens
    }
    FishSamplingEntryDialog {
        id: dlgFishSamplingEntry
    }
    NoteDialog {
        id: dlgNote
    }
}