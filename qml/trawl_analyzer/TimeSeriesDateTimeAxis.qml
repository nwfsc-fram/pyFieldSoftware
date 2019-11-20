import QtQuick 2.7
import QtCharts 2.1

DateTimeAxis {
    id: depthAxisX
    format: "HH:mm:ss"      // TODO Todd Hay - How to add date on a new line?
    min: timeSeries.xMin
    max: timeSeries.xMax
    labelsVisible: false
    gridVisible: true
    minorGridVisible: true
    tickCount: 10
}


