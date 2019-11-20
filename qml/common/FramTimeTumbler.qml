import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles.Flat 1.0 as Flat
import QtQuick.Extras 1.4
import QtQuick.Layouts 1.2

Tumbler {
    style: Flat.TumblerStyle {} // Use Flat style (could not find this properly documented anywhere)
    property int defaultCylinderWidth: 52 // Default determined by debug statement.
    property int cylinderWidth: defaultCylinderWidth

    function get_time_str() {
        var min_padding = colMin.currentIndex > 9 ? "" : "0";
        var timestr = colHour.currentIndex + ":" + min_padding + colMin.currentIndex;
        console.log("Time Tumbler " + timestr);
        return timestr;
    }

//    function set_time_str(time_str) {
//        var input_datetime = Date.fromLocaleTimeString(Qt.locale(), time_str, 'H:m');

//    }
    Component.onCompleted: {
        var curDate = new Date();
        setCurrentIndexAt(0, curDate.getHours());
        setCurrentIndexAt(1, curDate.getMinutes());
        //console.debug("Cylinder widths = " + colHour.width + "/" + colMin.width + ".");
    }

    TumblerColumn {
        id: colHour
        model: 24
        width: cylinderWidth
    }

    TumblerColumn {
        id: colMin
        model: getMins()
        width: cylinderWidth
        function getMins() {
            var mins = [];
            for (var i=0; i < 60; i++) {
                if (i < 10)
                    mins.push("0" + String(i));
                else
                    mins.push(String(i));
            }
            return mins;
        }
    }
}
