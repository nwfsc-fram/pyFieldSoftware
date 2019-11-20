import QtQuick 2.7
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.2
import QtQuick.Layouts 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Window 2.2

import "../common"

Item {
    id: root
    property int buttonHeight: 80
    property int buttonWidth: buttonHeight*2

    function setSpecies(species) {
        console.info('species is ' + species);
    }

    RowLayout {
        id: rlHeader
            spacing: 10
            anchors.top: parent.top
            anchors.topMargin: 10
            anchors.left: parent.left
            width: parent.width
            BackdeckButton {
                id: btnBack
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("<<")
                onClicked: {
                    screens.pop();
                }
            } // btnBack

            Label { Layout.fillWidth: true }

            BackdeckButton {
                id: btnWeighBaskets
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Weigh\nBaskets")
                onClicked: {
                    if (!screens.busy) {
                        screens.push(Qt.resolvedUrl("WeighBasketsScreen.qml"))
                        bdSM.to_fish_sampling_state()
                    }
                }
            } // btnWeighBaskets
            BackdeckButton {
                id: btnBioSampling
                Layout.preferredWidth: 120
                Layout.preferredHeight: 60
                text: qsTr("Bio\nSampling")
                onClicked: {
                    if (!screens.busy) {
                        screens.push(Qt.resolvedUrl("FishSamplingScreen.qml"))
                        bdSM.to_fish_sampling_state()
                    }
                }
            } // btnBioSampling

    }  // rlHeader

    GridLayout {
        id: glSpecies
        columns: 6
        rows: 5
        columnSpacing: 10
        rowSpacing: 10
        flow: GridLayout.TopToBottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        ExclusiveGroup { id: egSpecies }

        // Column 1
        BackdeckButton {
            id: btnBocaccio
            text: species
            property string species: qsTr("Bocaccio\nWt: 25kg")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnBocaccio
        BackdeckButton {
            id: btnVermilion
            text: species
            property string species: qsTr("Vermilion")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnVermilion
        BackdeckButton {
            id: btnGreenSpotted
            text: species
            property string species: qsTr("Greenspotted")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnGreenSpotted
        BackdeckButton {
            id: btnSpeckled
            text: species
            property string species: qsTr("Speckled")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnSpeckled
        BackdeckButton {
            id: btnBank
            text: species
            property string species: qsTr("Bank")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnBank

        // Column 2
        BackdeckButton {
            id: btnBlue
            text: species
            property string species: qsTr("Blue")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnBlue
        BackdeckButton {
            id: btnCaliforniaSheephead
            text: species
            property string species: qsTr("California\nSheephead")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnCaliforniaSheephead
        BackdeckButton {
            id: btnCanary2
            text: species
            property string species: qsTr("Canary")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnCanary
        BackdeckButton {
            id: btnChilipepper
            text: species
            property string species: qsTr("Chilipepper")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnChilipepper
        BackdeckButton {
            id: btnCopper
            text: species
            property string species: qsTr("Copper")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnCopper

        // Column 3
        BackdeckButton {
            id: btnCowcod
            text: species
            property string species: qsTr("Cowcod")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnCowcod
        BackdeckButton {
            id: btnFlag
            text: species
            property string species: qsTr("Flag")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnFlag
        BackdeckButton {
            id: btnGreenblotched
            text: species
            property string species: qsTr("Greenblotched")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnGreenblotched
        BackdeckButton {
            id: btnGreenstriped
            text: species
            property string species: qsTr("Greenstriped")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnGreenstriped
        BackdeckButton {
            id: btnHalfbanded
            text: species
            property string species: qsTr("Halfbanded")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnHalfbanded

        // Column 4
        BackdeckButton {
            id: btnHoneycomb
            text: species
            property string species: qsTr("Honeycomb")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnHoneycomb
        BackdeckButton {
            id: btnLingcod
            text: species
            property string species: qsTr("Lingcod")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnLingcod
        BackdeckButton {
            id: btnLizardfish
            text: species
            property string species: qsTr("Lizardfish")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnLizardfish
        BackdeckButton {
            id: btnOceanWhitefish
            text: species
            property string species: qsTr("Ocean\nWhitefish")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnOceanWhitefish
        BackdeckButton {
            id: btnOlive
            text: species
            property string species: qsTr("Olive")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnOlive

        // Column 5
        BackdeckButton {
            id: btnPacificMackerel
            text: species
            property string species: qsTr("Pacific\nMackerel")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnPacificMackerel
        BackdeckButton {
            id: btnRosy
            text: species
            property string species: qsTr("Rosy")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnRosy
        BackdeckButton {
            id: btnSanddab
            text: species
            property string species: qsTr("Sanddab")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnSanddab
        BackdeckButton {
            id: btnSquarespot
            text: species
            property string species: qsTr("Squarespot")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnSquarespot
        BackdeckButton {
            id: btnStarry
            text: species
            property string species: qsTr("Starry")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnStarry

        // Column 6
        BackdeckButton {
            id: btnSwordspine
            text: species
            property string species: qsTr("Swordspine")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnSwordspine
        BackdeckButton {
            id: btnWidow
            text: species
            property string species: qsTr("Widow")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnWidow
        BackdeckButton {
            id: btnYelloweye
            text: species
            property string species: qsTr("Yelloweye")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnYelloweye
        BackdeckButton {
            id: btnYellowtail
            text: species
            property string species: qsTr("Yellowtail")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: true
            checked: false
            onClicked: { setSpecies(species); }
        } // btnYellowtail
        BackdeckButton {
            id: btnSearch
            text: species
            property string species: qsTr("Search")
            Layout.preferredWidth: buttonWidth
            Layout.preferredHeight: buttonHeight
            activeFocusOnTab: false
            exclusiveGroup: egSpecies
            checkable: false
            onClicked: {  }
        } // btnSearch

    } // glSpecies

}