import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.2
import QtQuick.Window 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0


import "../common"

Dialog {
    id: dlg
    width: 1060
    height: 600
    title: "Fish Sampling Entry"

    onRejected: {  }
    onAccepted: {
        clearTabs();
    }
    function clearTabs() {
        var item;
        var action;
        for (var i=0; i<tvActions.count; i++) {
            item = tvActions.getTab(i).item;
            action = tvActions.getTab(i).action;
            tvActions.getTab(i).title = action;
            if (item !== null) {
                switch (action) {
                    case "A-D-H":
                        item.angler = ""
                        item.drop = ""
                        item.hook = ""
                        item.egAngler.current = null;
                        item.egDrop.current = null;
                        item.egHook.current = null;
                        break;
                    case "Species":
                        item.egSpecies.current = null;
                        break;
                    case "Weight":
                        item.numPad.textNumPad.text = "";
                        break;
                    case "Length":
                        item.numPad.textNumPad.text = "";
                        break;
                    case "Sex":
                        item.egSexType.current = null;
                        break;
                    case "Otolith":
                        item.egAgeStructure.current = item.btnOtolith;
                        item.numPad.textNumPad.text = "";
                        break;
                    case "Finclip":
                        item.egFinclipCategory.current = null;
                        item.numPad.textNumPad.text = "";
                        break;
                    case "Disposition":
                        item.egDisposition.current = item.btnSacrificed;
                        item.numPad.textNumPad.text = "";
                        break;
                    case "Special":
                        item.numPad.textNumPad.text = "";
                        break;
                }
            }
            tvActions.currentIndex = 0;
        }
    }

    contentItem: Rectangle {
//        color: SystemPaletteSingleton.window(true)
        color: "#eee"

        ColumnLayout {
            spacing: 25
            anchors.fill: parent
            TabView {
                id: tvActions
                anchors.top: parent.top
                anchors.topMargin: 10
                Layout.preferredWidth: parent.width
                Layout.fillHeight: true

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
                            horizontalAlignment: Text.AlignHCenter
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
                    id: tabADH
                    title: qsTr("A-D-H")
                    active: true
                    property string action: "A-D-H"
                    property int buttonSize: 70
                    Item {
                        property string angler: ""
                        property string drop: ""
                        property string hook: ""
                        property alias egAngler: egAngler
                        property alias egDrop: egDrop
                        property alias egHook: egHook
                        function setLabel(component, value) {
                            switch (component) {
                                case "angler":
                                    angler = value;
                                    break;
                                case "drop":
                                    drop = value;
                                    break;
                                case "hook":
                                    hook = value;
                                    break;
                            }
                            parent.title = action + "\n" + angler + drop + hook;
                            if ((angler !== "") && (drop !== "") && (hook !== "") &&
                                (tvActions.currentIndex < tvActions.count - 1)) {
                                tvActions.currentIndex = tvActions.currentIndex + 1;
                            }
                        }
                        GridLayout {
                            columns: 3
                            rows: 6
                            columnSpacing: 60
                            rowSpacing: 10
                            flow: GridLayout.TopToBottom
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.verticalCenter: parent.verticalCenter
                            ExclusiveGroup { id: egAngler }
                            ExclusiveGroup { id: egDrop }
                            ExclusiveGroup { id: egHook }

                            // Column 1
                            Label { text: qsTr("Angler"); font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter; }
                            BackdeckButton {
                                id: btnAnglerA
                                text: qsTr("A")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egAngler
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("angler", text);
                                }
                            } // btnAnglerA
                            BackdeckButton {
                                id: btnAnglerB
                                text: qsTr("B")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egAngler
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("angler", text);
                                }
                            } // btnAnglerB
                            BackdeckButton {
                                id: btnAnglerC
                                text: qsTr("C")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egAngler
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("angler", text);
                                }
                            } // btnAnglerC
                            Label {}
                            Label {}

                            // Column 2
                            Label { text: qsTr("Drop"); font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter; }
                            BackdeckButton {
                                id: btnDrop1
                                text: qsTr("1")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egDrop
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("drop", text);
                                }
                            } // btnDrop1
                            BackdeckButton {
                                id: btnDrop2
                                text: qsTr("2")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egDrop
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("drop", text);
                                }
                            } // btnDrop2
                            BackdeckButton {
                                id: btnDrop3
                                text: qsTr("3")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egDrop
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("drop", text);
                                }
                            } // btnDrop3
                            BackdeckButton {
                                id: btnDrop4
                                text: qsTr("4")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egDrop
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("drop", text);
                                }
                            } // btnDrop4
                            BackdeckButton {
                                id: btnDrop5
                                text: qsTr("5")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egDrop
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("drop", text);
                                }
                            } // btnDrop5

                            // Column 3
                            Label { text: qsTr("Hook"); font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter; }
                            BackdeckButton {
                                id: btnHook1
                                text: qsTr("1")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egHook
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("hook", text);
                                }
                            } // btnHook1
                            BackdeckButton {
                                id: btnHook2
                                text: qsTr("2")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egHook
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("hook", text);
                                }
                            } // btnHook2
                            BackdeckButton {
                                id: btnHook3
                                text: qsTr("3")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egHook
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("hook", text);
                                }
                            } // btnHook3
                            BackdeckButton {
                                id: btnHook4
                                text: qsTr("4")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egHook
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("hook", text);
                                }
                            } // btnHook4
                            BackdeckButton {
                                id: btnHook5
                                text: qsTr("5")
                                Layout.preferredWidth: buttonSize
                                Layout.preferredHeight: buttonSize
                                exclusiveGroup: egHook
                                checkable: true
                                checked: false
                                activeFocusOnTab: false
                                onClicked: {
                                    setLabel("hook", text);
                                }
                            } // btnHook5
                        }
                    }
                } // tabADH
                Tab {
                    id: tabSpecies
                    title: action
                    active: true
                    property string action: "Species"
                    property int buttonHeight: 80
                    property int buttonWidth: buttonHeight*2
                    Item {
                        property alias egSpecies: egSpecies
                        function setSpecies(species) {
                            parent.title = action + "\n" + species;
                            if (tvActions.currentIndex < tvActions.count - 1)
                                tvActions.currentIndex = tvActions.currentIndex + 1;
                        }
                        GridLayout {
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
                                property string species: qsTr("Bocaccio")
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

                        }
                    }
                } // tabSpecies
                Tab {
                    id: tabWeight
                    title: action
                    active: true
                    property string action: "Weight"
                    onVisibleChanged: {
                        if (this.visible) {
                            this.item.numPad.textNumPad.selectAll();
                        }
                    }
                    Item {
                        property alias numPad: numPad;
                        FramNumPad {
                            id: numPad
                            x: parent.width/2 - 180
                            y: 5
                            state: qsTr("weights")
                            onNumpadok: {
                                parent.parent.title = action + "\n" + numPad.textNumPad.text + " kg";
                                if (tvActions.currentIndex < tvActions.count - 1)
                                    tvActions.currentIndex = tvActions.currentIndex + 1;
                            }
                        } // numPad
                    }
                } // tabWeight
                Tab {
                    id: tabLength
                    title: action
                    active: true
                    property string action: "Length"
                    onVisibleChanged: {
                        if (this.visible) {
                            this.item.numPad.textNumPad.selectAll();
                        }
                    }
                    Item {
                        property alias numPad: numPad;
                        FramNumPad {
                            id: numPad
                            x: parent.width/2 - 180
                            y: 5
                            state: qsTr("weights")
                            onNumpadok: {
                                parent.parent.title = action + "\n" + numPad.textNumPad.text + " cm";
                                if (tvActions.currentIndex < tvActions.count - 1)
                                    tvActions.currentIndex = tvActions.currentIndex + 1;
                            }
                        } // numPad
                    }
                } // tabLength
                Tab {
                    id: tabSex
                    title: action
                    property string action: "Sex"
                    property int buttonHeight: 70
                    property int buttonWeight: 2*buttonHeight
                    Item {
                        property alias egSexType: egSexType
                        function changeSex(value) {
                            parent.title = action + "\n" + value;
                            if (tvActions.currentIndex < tvActions.count - 1)
                                tvActions.currentIndex = tvActions.currentIndex + 1;
                        }
                        RowLayout {
                            id: rlSex
                            spacing: 20
                            Layout.fillWidth: false
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.verticalCenter: parent.verticalCenter
                            ExclusiveGroup { id: egSexType }
                            TrawlBackdeckButton {
                                id: btnFemale
                                text: qsTr("Female")
                                checked: false
                                checkable: true
                                exclusiveGroup: egSexType
                                Layout.preferredWidth: buttonWeight
                                Layout.preferredHeight: buttonHeight
                                onClicked: changeSex("F")
                                activeFocusOnTab: false
                            } // btnFemale
                            TrawlBackdeckButton {
                                id: btnMale
                                text: qsTr("Male")
                                checkable: true
                                exclusiveGroup: egSexType
                                Layout.preferredWidth: buttonWeight
                                Layout.preferredHeight: buttonHeight
                                onClicked: changeSex("M")
                                activeFocusOnTab: false
                            } // btnMale
                            TrawlBackdeckButton {
                                id: btnUnsex
                                text: qsTr("Unsex")
                                checkable: true
                                exclusiveGroup: egSexType
                                Layout.preferredWidth: buttonWeight
                                Layout.preferredHeight: buttonHeight
                                onClicked: changeSex("U")
                                activeFocusOnTab: false
                            } // btnUnsex
                        }
                    }
                } // tabSex
                Tab {
                    id: tabAge
                    title: action
                    active: true
                    property string action: "Otolith"
                    onVisibleChanged: {
                        if (this.visible) {
                            this.item.numPad.textNumPad.selectAll();
                        }
                    }
                    Item {
                        property alias egAgeStructure: egAgeStructure
                        property alias btnOtolith: btnOtolith
                        property alias numPad: numPad;
                        ColumnLayout {
                            x: 20
                            y: 20
                            ExclusiveGroup {
                                id: egAgeStructure
                            }
                            Label {
                                text: qsTr("Structure Type")
                                font.pixelSize: 20
                                Layout.preferredWidth: 100
                            }
                            BackdeckButton {
                                id: btnOtolith
                                text: qsTr("Otolith")
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                checked: true
                                checkable: true
                                activeFocusOnTab: false
                                exclusiveGroup: egAgeStructure
                            } // btnOtolith
                            BackdeckButton {
                                id: btnFinray
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                text: qsTr("Finray")
                                checked: false
                                checkable: true
                                activeFocusOnTab: false
                                exclusiveGroup: egAgeStructure
                            } // btnFinray
                            BackdeckButton {
                                id: btnSecondDorsalSpine
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                text: qsTr("2nd Dorsal\nSpine")
                                checked: false
                                checkable: true
                                activeFocusOnTab: false
                                exclusiveGroup: egAgeStructure
                            } // btnSecondDorsalSpine
                            BackdeckButton {
                                id: btnVertebra
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                text: qsTr("Vertebra")
                                checked: false
                                checkable: true
                                activeFocusOnTab: false
                                exclusiveGroup: egAgeStructure
                            } // btnVertebra
                            BackdeckButton {
                                id: btnScale
                                text: qsTr("Scale")
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                checked: false
                                checkable: true
                                activeFocusOnTab: false
                                exclusiveGroup: egAgeStructure
                            } // btnScale
                            BackdeckButton {
                                id: btnNotAvailable
                                text: qsTr("Not\nAvailable")
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                checked: false
                                checkable: true
                                activeFocusOnTab: false
                                exclusiveGroup: egAgeStructure
                            } // btnNotAvailable
                        }
                        FramNumPad {
                            id: numPad
                            x: parent.width/2 - 180
                            y: 5
                            state: qsTr("counts")
                            onNumpadok: {
                                parent.parent.title = action + "\n" + numPad.textNumPad.text;
                                if (tvActions.currentIndex < tvActions.count - 1)
                                    tvActions.currentIndex = tvActions.currentIndex + 1;
                            }
                        } // numPad
                    }
                } // tabAge
                Tab {
                    id: tabFinclip
                    title: action
                    active: true
                    property string action: "Finclip"
                    onVisibleChanged: {
                        if (this.visible) {
                            this.item.numPad.textNumPad.selectAll();
                        }
                    }
                    Item {
                        property alias numPad: numPad;
                        property int buttonSize: 70
                        property string type: "A"
                        property variant num: null
                        property alias egFinclipCategory: egFinclipCategory
                        function setFinclip(category, value) {
                            switch (category) {
                                case "type":
                                    type = value;
                                    break;
                                case "num":
                                    num = value;
                                    break;
                            }
                            if ((type !== "") && (num !== null)) {
                                parent.title = action + "\n" + type + num;
                                if (tvActions.currentIndex < tvActions.count - 1)
                                    tvActions.currentIndex = tvActions.currentIndex + 1;
                            }
                        }
                        ColumnLayout {
                            id: clFinclipCategory
//                            anchors.horizontalCenter: parent.horizontalCenter
                            x: parent.width/4
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 20
                            ExclusiveGroup {
                                id: egFinclipCategory
                            }
                            BackdeckButton {
                                id: btnFinclipB
                                text: qsTr("B")
                                Layout.preferredHeight: buttonSize
                                Layout.preferredWidth: buttonSize * 2
                                checkable: true
                                checked: false
                                exclusiveGroup: egFinclipCategory
                                activeFocusOnTab: false
                                onClicked: {
                                    setFinclip("type", "B");
                                }
                            } // btnFinclipB
                            BackdeckButton {
                                id: btnFinclipV
                                text: qsTr("V")
                                Layout.preferredHeight: buttonSize
                                Layout.preferredWidth: buttonSize * 2
                                checkable: true
                                checked: false
                                exclusiveGroup: egFinclipCategory
                                activeFocusOnTab: false
                                onClicked: {
                                    setFinclip("type", "V");
                                }
                            } // btnFinclipV
                            BackdeckButton {
                                id: btnFinclipG
                                text: qsTr("G")
                                Layout.preferredHeight: buttonSize
                                Layout.preferredWidth: buttonSize * 2
                                checkable: true
                                checked: false
                                exclusiveGroup: egFinclipCategory
                                activeFocusOnTab: false
                                onClicked: {
                                    setFinclip("type", "G");
                                }
                            } // btnFinclipG
                            BackdeckButton {
                                id: btnFinclipA
                                text: qsTr("A")
                                Layout.preferredHeight: buttonSize
                                Layout.preferredWidth: buttonSize * 2
                                checkable: true
                                checked: true
                                exclusiveGroup: egFinclipCategory
                                activeFocusOnTab: false
                                onClicked: {
                                    setFinclip("type", "A");
                                }
                            } // btnFinclipA
                        }
                        FramNumPad {
                            id: numPad
                            x: parent.width/2 - 50
                            y: 5
                            state: qsTr("counts")
                            onNumpadok: {
                                setFinclip("num", numPad.textNumPad.text);
                            }
                        } // numPad
                    }
                } // tabFinclip
                Tab {
                    id: tabDisposition
                    title: action + "\nSacrificed"
                    active: true
                    property string action: "Disposition"
                    onVisibleChanged: {
                        if (this.visible) {
                            this.item.numPad.textNumPad.selectAll();
                        }
                    }
                    Item {
                        property alias numPad: numPad;
                        property alias egDisposition: egDisposition
                        property alias btnSacrificed: btnSacrificed
                        function setDisposition(value) {
                            numPad.enabled = (value === "Sacrificed") ? false : true;
                            parent.title = action + "\n" + value;
                            if (((value === "Released" || value === "Descended") &&
                                (numPad.textNumPad.text !== null &&
                                    numPad.textNumPad.text !== "0")) ||
                                    (value === "Sacrificed")) {
                                if (tvActions.currentIndex < tvActions.count - 1) {
                                    tvActions.currentIndex = tvActions.currentIndex + 1;
                                }
                            }
                            if (value === "Sacrificed") {
                                numPad.textNumPad.text = "0"
                            }
                        }
                        ColumnLayout {
                            spacing: 20
                            x: parent.width/4
                            anchors.verticalCenter: parent.verticalCenter
                            ExclusiveGroup { id: egDisposition }
                            BackdeckButton {
                                id: btnSacrificed
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                text: qsTr("Sacrificed")
                                activeFocusOnTab: false
                                exclusiveGroup: egDisposition
                                checkable: true
                                checked: true
                                onClicked: { setDisposition("Sacrificed"); }
                            } // btnSacrificed
                            BackdeckButton {
                                id: btnReleased
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                text: qsTr("Released\nat Surface")
                                activeFocusOnTab: false
                                exclusiveGroup: egDisposition
                                checkable: true
                                checked: false
                                onClicked: { setDisposition("Released"); }
                            } // btnReleased
                            BackdeckButton {
                                id: btnDescended
                                Layout.preferredWidth: 120
                                Layout.preferredHeight: 60
                                text: qsTr("Descended")
                                activeFocusOnTab: false
                                exclusiveGroup: egDisposition
                                checkable: true
                                checked: false
                                onClicked: { setDisposition("Descended"); }
                            } // btnDescended
                        }
                        Label {
                            text: qsTr("Tag Number")
                            font.pixelSize: 20
                            anchors.centerIn: parent
                            horizontalAlignment: Text.AlignHCenter
                            rotation: 270
                        }
                        FramNumPad {
                            id: numPad
                            x: parent.width/2 + 40
                            y: 5
                            enabled: false
                            state: qsTr("counts")
                            onNumpadok: {
                                if (tvActions.currentIndex < tvActions.count - 1) {
                                    tvActions.currentIndex = tvActions.currentIndex + 1;
                                }
                            }
                        } // numPad
                    }
                } // tabDisposition
                Tab {
                    id: tabSpecial
                    title: action
                    active: true
                    property string action: "Special"
                    onVisibleChanged: {
                        if (this.visible) {
                            this.item.numPad.textNumPad.selectAll();
                        }
                    }
                    Item {
                        property alias numPad: numPad;
                        FramNumPad {
                            id: numPad
                            x: parent.width/2 - 180
                            y: 5
                            state: qsTr("counts")
                            onNumpadok: {
                                parent.parent.title = action + "\n" + numPad.textNumPad.text;
                                if (tvActions.currentIndex < tvActions.count - 1)
                                    tvActions.currentIndex = tvActions.currentIndex + 1;
                            }
                        } // numPad
                    }
                } // tabSpecial

            }
            RowLayout {
                id: rlButtons
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 10
                anchors.right: parent.right
                anchors.rightMargin: 10
                spacing: 10
                BackdeckButton {
                    id: btnNotes
                    text: "Notes"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    onClicked: { }
                } // btnNotes
                BackdeckButton {
                    id: btnNextFish
                    text: "Next Fish"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    onClicked: { clearTabs(); }
                } // btnNextFish
                BackdeckButton {
                    id: btnFinished
                    text: "Finished"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 60
                    onClicked: { dlg.accept() }
                } // btnFinished
            } // rlButtons
        }

        Keys.onEnterPressed: dlg.accept()
        Keys.onReturnPressed: dlg.accept()
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
