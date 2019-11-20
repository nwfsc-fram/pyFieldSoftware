import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.3
import ".."

Item {
    property string action: "species";

    property int buttonBaseSize: 80
    property alias sfl1: sfl1
    property alias sfl2: sfl2
    property alias sfl3: sfl3
    property alias bgSpecies: bgSpecies;
    property var currentSpecies: null;

    signal labelSet(string action, variant value, string uom, bool dbUpdate, variant actionSubType);
    signal advanceTab();

    Connections {
        target: sfl1
        onSpeciesSelected: setSpecies(species)
    } // sfl1.onSpeciesSelected
    Connections {
        target: sfl2
        onSpeciesSelected: setSpecies(species)
    } // sfl2.onSpeciesSelected
    Connections {
        target: sfl3
        onSpeciesSelected: setSpecies(species)
    } // sfl3.onSpeciesSelected

    function setSpecies(species) {
        currentSpecies = species;
        labelSet(action, species, null, true, null);
//        advanceTab();
    }
    ButtonGroup { id: bgSpecies }

    SpeciesFullList {
        id: sfl1
        repeaterIndex: 0
        visible: true
    } // sfl1
    SpeciesFullList {
        id: sfl2
        repeaterIndex: 1
        visible: false
    } // sfl2
    SpeciesFullList {
        id: sfl3
        repeaterIndex: 2
        visible: false
    } // sfl3

    PageIndicator {
        id: piIndicator
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        count: 3
        currentIndex: 0

        delegate: Rectangle {
            implicitWidth: 80
            implicitHeight: 80

            property variant alphaIndex: {0: "A-G", 1: "G-S", 2: "S-Y"}
            radius: width
            color: "white"
            border.color: "black"
            border.width: 5

            opacity: index === piIndicator.currentIndex ? 0.95 : pressed ? 0.5 : 0.3

            Behavior on opacity {
                OpacityAnimator {
                    duration: 100
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    if (index != piIndicator.currentIndex) {
                        piIndicator.currentIndex = index;
                        sfl1.visible = false;
                        sfl2.visible = false;
                        sfl3.visible = false;
                        switch (index) {
                            case 0:
                                sfl1.visible = true;
                                break;
                            case 1:
                                sfl2.visible = true;
                                break;
                            case 2:
                                sfl3.visible = true;
                                break;
                        }
                    }
                }
            }
            Text {
                text: alphaIndex[index]
                color: "black"
                font.pixelSize: 24
                font.bold: true
                anchors.fill: parent
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

}