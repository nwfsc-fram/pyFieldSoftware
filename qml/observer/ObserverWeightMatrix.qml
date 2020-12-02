import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4

// Custom Model
import "../common"
import "."

Item {
    id: wtMatrix
    property alias step: wtMatrix.step
    property alias lowerRange: wtMatrix.lowerRange
    property alias upperRange: wtMatrix.upperRange
    property real lowerRange: 0.25  // adjust these if range adjustment needed
    property real upperRange: 21
    property real step: 0.25
    property bool enable_audio: false

    signal weightClicked(real weight)

    function createModel() {
        var arr = []
        for (var i = wtMatrix.lowerRange; i <= wtMatrix.upperRange; i += wtMatrix.step) {
            arr.push(i)
        }
        return arr
    }
    ScrollView   {
        id: sv
        width: (ScreenUnits.numPadButtonSize * 4) + (gridMatrix.columnSpacing * 4) + 20
        height: (ScreenUnits.numPadButtonSize * 5) + (gridMatrix.rowSpacing * 5)
        GridLayout {
            id: gridMatrix
            columnSpacing: 6
            rowSpacing: 6
            columns: 4
            rows: (wtMatrix.upperRange - wtMatrix.lowerRange) / gridMatrix.columns
            Repeater {
                id: rptMatrixBtns
                model: wtMatrix.createModel()
                FramNumPadButton {
                    text: modelData.toFixed(2)
                    Layout.preferredWidth: ScreenUnits.numPadButtonSize
                    Layout.preferredHeight: ScreenUnits.numPadButtonSize
                    onClicked: {
                        console.info("Weight clicked is " + modelData.toFixed(2))
                        weightClicked(modelData.toFixed(2))
                        if (enable_audio) {
                            soundPlayer.play_sound("matrixWtSel", false)
                        }
                    }
                }
            }
        }
    }
}