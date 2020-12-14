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
    id: matrix
    property bool enable_audio: false
    property real increment: 0.25
    property real lowerRange: 0.25
    property real upperRange: 40.0
    property int precision: 2  // allows adjustment of level of precision (e.g. 2.00 (2) vs 2 (0))
    property int buttonWidth: ScreenUnits.numPadButtonSize
    property int buttonHeight: ScreenUnits.numPadButtonSize
    property int columns: 4
    property int visibleRows: 5
    property var storedModels // store models to speed things up, rather than create on the fly
    property alias currentModel: rptMatrixBtns.model
    property alias matrixWidth: sv.width
    property alias matrixHeight: sv.height

    signal valClicked(real val)  // signal passes value stripped from button

    Component.onCompleted: {
    // load up default model from parameters defined above
        storedModels = {}
        matrix.addModel(increment, lowerRange, upperRange)  // add default model
        matrix.setModel(increment)  // set default model
    }

    function setModel(incr) {
    // use for toggling model in matrix
        if (storedModels[incr]) {
            matrix.increment = incr
            rptMatrixBtns.model = storedModels[incr]
            console.info("Matrix model incremented by " + incr)
        } else {
            console.info("Increment model " + incr + " has not been created yet!  Please use 'addModel' func")
        }
    }
    function addModel(incr, lr, ur) {
        // incase you wanted to add custom model, or overwrite existing
        storedModels[incr] = matrix.createModel(incr, lr, ur)
        console.debug("New matrix model stored: increment=" + increment + ", " + lr + " - " + ur)
    }

    function createModel(incr, lr, ur) {
        // loop, step, and push (better way to do this??)
        var arr = []
        for (var i = lr; i <= ur; i+= incr) {
            arr.push(i)
        }
        return arr
    }

    ScrollView   {
        // TODO: Make this scalable/flexible with window movements
        // TODO: function to customize button colors within a range?
        id: sv
        width: (ScreenUnits.numPadButtonSize * matrix.columns) + (gridMatrix.columnSpacing * matrix.columns) + 20
        height: (ScreenUnits.numPadButtonSize * matrix.visibleRows) + (gridMatrix.rowSpacing * matrix.visibleRows)
        GridLayout {
            id: gridMatrix
            flow: GridLayout.LeftToRight
            columnSpacing: 6
            rowSpacing: 6
            columns: matrix.columns
            Repeater {
                id: rptMatrixBtns
                Button {
                    id: mtxBtn
                    Layout.preferredWidth: matrix.buttonWidth
                    Layout.preferredHeight: matrix.buttonHeight
                    style: ButtonStyle {
                        label: Component {
                            Text {
                                renderType: Text.NativeRendering
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                font.family: "Helvetica"
                                font.pixelSize: ScreenUnits.numPadButtonTextHeight
                                text: modelData.toFixed(matrix.precision)
                            }
                        }
                    }
                    onClicked: {
                        console.info("Matrix value clicked: " + modelData.toFixed(matrix.precision))
                        valClicked(modelData.toFixed(matrix.precision))
                        if (enable_audio) {
                            soundPlayer.play_sound("matrixSel", false)
                        }
                    }
                }
            }
        }
    }
}