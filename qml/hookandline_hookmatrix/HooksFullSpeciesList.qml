import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.2
import QtQuick.Controls.Private 1.0

Item {
    property int repeaterIndex: repeaterIndex

    GridLayout {
        rows: 6
        columns: 4
        rowSpacing: 10
        columnSpacing: 10

        Repeater {
            model: hooks.fullSpeciesListModel.getSubset(repeaterIndex);
            BackdeckButton {
                Layout.preferredWidth: buttonWidth
                Layout.preferredHeight: buttonHeight
                text: modelData.text.length > 13 ?
                        modelData.text.replace(" ", "\n") :
                        modelData.text;
                onClicked: {
                    populateHook(text.replace('\n', ' '));
                }
            }
        }
    }
}
