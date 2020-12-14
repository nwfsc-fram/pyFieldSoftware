import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Window 2.2
import QtQuick.Extras 1.4

// Custom Model
import "../common"
import "."

// TODO: Use ObserverMatrix instead of this in CountsWeights matrix

Item {
    id: wtMatrix
    // set default values
    property bool enable_audio: false
    property real increment: 0.25
    property real lowerRange: 0.25
    property real upperRange: 40.0
    property var storedModels // store models to speed things up, rather than create on the fly
    signal weightClicked(real weight)

    Component.onCompleted: {
        storedModels = {}
        // load up default model from parameters defined above
        wtMatrix.addModel(increment, lowerRange, upperRange)  // add default model
        wtMatrix.setModel(increment)  // set default model
    }

    function setModel(incr) {
        // use for toggling model in matrix TODO: error handle invalid key?
        rptMatrixBtns.model = storedModels[incr]
        console.info("Wt Matrix model incremented by " + incr)
    }

    function addModel(incr, lr, ur) {
        // incase you wanted to add custom model, or overwrite existing
        storedModels[incr] = wtMatrix.createModel(incr, lr, ur)
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
                model: wtMatrix.quartersModel  // default is 0.25 increments
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