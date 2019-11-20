pragma Singleton
import QtQuick 2.5

import "."
import "../common"   // For CommonUtil

Item {
    id: observerSettings
    function page_state_id() { // for transitions
        return "settings_state";
    }
    property date curDate: new Date()

    property string dateformat: "MM/dd/yyyy HH:MM"

    // For assisting manual UI tests (prepopulate views)
    property bool run_tests: false

    // Intended for full automated UI test suite
    property bool run_automated_tests: false

    // For various stuff for testing
    property bool test_mode: true
    property bool startup_small_window: true // Non-maximized window etc - false for prod build
    property bool allow_bad_password: appstate.isTestMode

    property string default_bgcolor: "#CCCCCC"
    property string datestringFormat: "YYYY-MM-DDTHH:MM:SS"  // ISO-something

    property int default_tf_height: 50

    // Formatting of lat or long minutes in LogBook and Locations
    property bool includeLeadingZeroInMinutes: true
    property int nDecimalPlacesInMinutes: 2

    property bool enableAudio: true

    function test() {
        console.log(curDateStr());
    }

    function newDate() {
        curDate = new Date()
        return curDate;
    }

    function curDateStr() {
        return Qt.formatDateTime(curDate, dateformat);
    }

    function iso_to_local(datestr) {
        // take DB formatted ISO string and convert to local locale Date
        return Date.fromLocaleString(Qt.locale(),
                                     datestr,
                                     "yyyy-MM-ddThh:mm:ss");  // convert from string
    }
    function str_to_local(datestr) {
            // take DB formatted ISO string and convert to local locale Date
            return Date.fromLocaleString(Qt.locale(),
                                         datestr,
                                         "MM/dd/yyyy hh:mm");  // convert from string
    }

    // function get_date_str(dateobj) moved to common/CommonUtil.

    function format_date(date_time_obj) {
        // Helper function for text display in QML
        if (date_time_obj) {
            var selected_date = iso_to_local(date_time_obj)
            return CommonUtil.get_date_str(selected_date);
        } else {
            return ""
        }
    }

}
