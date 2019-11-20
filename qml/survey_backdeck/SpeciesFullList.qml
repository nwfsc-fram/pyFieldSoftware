import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0

Item {
    property int repeaterIndex: repeaterIndex;
    property int buttonBaseSize: 80;
    property alias glSpecies: glSpecies;

    signal speciesSelected(string species)

    GridLayout {
        id: glSpecies
        rows: 4
        columns: 6
        rowSpacing: 10
        columnSpacing: 10

        Repeater {
            model: fishSampling.speciesFullListModel.getSubset(repeaterIndex);
            BackdeckButton2 {
                ButtonGroup.group: bgSpecies
                checkable: true
                Layout.preferredWidth: buttonBaseSize * 2
                Layout.preferredHeight: buttonBaseSize
                text: modelData.text.length > 13 ?
                        modelData.text.replace(" ", "\n") :
                        modelData.text;
                onClicked: {
//                    var truncSpecies = text.length > 11 ?
//                         text.substring(0,11).replace('\n', ' ') :
//                         text.replace('\n', '')
//                    speciesSelected(truncSpecies);
                    speciesSelected(text);
                }
            }
        }
    }
}
