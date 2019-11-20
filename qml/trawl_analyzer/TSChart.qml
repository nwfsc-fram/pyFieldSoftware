import QtQuick 2.7
import QtQuick.Layouts 1.1
import QtCharts 2.1

Item {

    ValueAxis {
        id: axisX1
        min:  0
        max: 10
        labelsVisible: false
    } // axisX1
    ValueAxis {
        id: axisX2
        min:  0
        max: 10
        labelsVisible: false
    } // axisX2
    ValueAxis {
        id: axisY1
        min:  0
        max: 10
    } // axisY1
    ValueAxis {
        id: axisY2
        min:  0
        max: 1000
    } // axisY2

    ColumnLayout {
        width: parent.width
        spacing: 0

        ChartView {
            id: cv1
            antialiasing: true

            Layout.preferredWidth: parent.width
            Layout.preferredHeight: 200

            backgroundRoundness: 0

            margins.top: 0
            margins.bottom: 0
            margins.right: 0
            margins.left: 0

            legend.alignment: Qt.AlignRight

            LineSeries {
                id: lineSeries1
                name: "signal 1"
                axisX: axisX1
                axisY: axisY1
                XYPoint { x: 0; y: 0 }
                XYPoint { x: 1.1; y: 2.1 }
                XYPoint { x: 1.9; y: 3.3 }
                XYPoint { x: 2.1; y: 2.1 }
                XYPoint { x: 2.9; y: 4.9 }
                XYPoint { x: 3.4; y: 3.0 }
                XYPoint { x: 4.1; y: 3.3 }
            }
        }
        ChartView {
            id: cv2
            antialiasing: true
            backgroundRoundness: 0

            Layout.preferredWidth: parent.width
            Layout.preferredHeight: 200

            margins.top: 0
            margins.bottom: 0
            margins.right: 0
            margins.left: 0

            legend.alignment: Qt.AlignRight

            LineSeries {
                id: lineSeries2
                name: "A second signal, longer title"
                axisX: axisX2
                axisY: axisY2
                XYPoint { x: 0; y: 0 }
                XYPoint { x: 1.4; y: 200.1 }
                XYPoint { x: 2.4; y: 300.3 }
                XYPoint { x: 3.1; y: 300.1 }
                XYPoint { x: 3.3; y: 400.9 }
                XYPoint { x: 3.8; y: 500.0 }
                XYPoint { x: 4.7; y: 450.3 }
            }
        }

    }
}


